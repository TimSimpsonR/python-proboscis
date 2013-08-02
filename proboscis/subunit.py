"""
Contains methods and classes to make a Proboscis test suite compatable with
Test Repository, subunit, and its friends.

There's two methods to achieve parallel execution using testr:

1. Ask it to only all tests which depend on each other in some way in the
   same process. This way nothing breaks, though the bottleneck becomes the
   slowest executing chain of tests.
2. Change every test which is a dependency to a test resource. I'm not sure
   yet how to handle "runs_after" situations where tests may check things
   are cleaned up. It's def. not a one-to-one mapping.

For now, this module attempts style #1.

"""
from __future__ import absolute_import

import sys
import unittest

from subunit import TestProtocolClient


from proboscis.case import TestInitiator
from proboscis.case import TestSuiteCreator



class ProcOrganizer(object):

    def __init__(self, plan):
        self.case_to_proc = {}
        self.procs = []
        index = 0
        for case in plan.tests:
            case._order = index
            index += 1
            self.place_case(case)

    def get_proc(self, case):
        proc = self.case_to_proc.get(case)
        if not proc:
            proc = set((case, ))
            self.procs.append(proc)
            self.case_to_proc[case] = proc
        return proc

    def move_case_to_proc(self, case, proc):
        def change_refs(old_p, new_p):
            for c in old_p:
                self.case_to_proc[c] = new_p
            self.procs = [ p for p in self.procs if p is not old_p]

        if case not in self.case_to_proc:
            proc.add(case)
            self.case_to_proc[case] = proc
        elif case in proc:
            return
        else:
            old_proc = self.case_to_proc[case]
            new_proc = proc.union(old_proc)
            self.procs.append(new_proc)
            change_refs(old_proc, new_proc)
            change_refs(proc, new_proc)

    def place_case(self, case):
        proc = self.get_proc(case)
        for dep in case.dependents:
            self.move_case_to_proc(dep.case, proc)



def should_run(case):
    return case.entry.info.enabled and case.entry.home is not None


def is_root_case(case):
    info = case.entry.info
    return not (info.depends_on or info.depends_on_groups)

# def create_testr_parallel_suite(plan, test_loader=None, root_suite=None):
#     """
#     Given a plan, creates a test suite which has only top level entries which
#     are themselves suites. The idea is that each of these suites could then
#     run in a seperate process as they are an independent chain of dependencies.
#     """
#     test_loader = test_loader or unittest.TestLoader()
#     #root_suite = root_suite or unittest.TestSuite()
#     root_suite = unittest.TestSuite()
#     creator = TestSuiteCreator(test_loader)
#     for case in plan.tests:
#         info = case.entry.info
#         if should_run(case) and is_root_case(case):
#             suite = create_testr_nested_suite(creator, case)
#             root_suite.addTest(suite)
#     return root_suite

def create_testr_parallel_suite(plan, test_loader=None, root_suite=None):
    """
    Given a plan, creates a test suite which has only top level entries which
    are themselves suites. The idea is that each of these suites could then
    run in a seperate process as they are an independent chain of dependencies.
    """
    test_loader = test_loader or unittest.TestLoader()
    #root_suite = root_suite or unittest.TestSuite()
    root_suite = unittest.TestSuite()
    creator = TestSuiteCreator(test_loader)
    procs = ProcOrganizer(plan).procs
    for proc in procs:
        from subunit import IsolatedTestSuite
        proc_suite = IsolatedTestSuite()
        cases = sorted(list(proc), key=lambda x : x._order)
        for case in cases:
            add_case_to_suite(creator, case, proc_suite)
        root_suite.addTest(proc_suite)
    return root_suite


def add_case_to_suite(creator, case, suite):
    tests = creator.loadTestsFromTestEntry(case)
    for test in tests:
        suite.addTest(test)


def create_testr_nested_suite(creator, case, suite=None, dependents=None,
                              next_dependents=None):
    """
    Given a creator function which can load tests from a Proboscis test entry,
    and a test case which has dependents, creates a suite. The idea is that
    this suite could run in it's own process where one thing dependents on
    another.
    The other idea is that for TestR discovery, this suite will appear by
    itself during the discovery phase without advertising its children,
    so that TestR will run it alone. When it is actually run it will begin to
    run all of it's nested children which will all be reported as test
    results.
    """
    from subunit import IsolatedTestSuite
    suite = suite or IsolatedTestSuite()
    add_case_to_suite(creator, case, suite)
    dependents = dependents or []
    next_dependents = next_dependents or []
    new_dependents = dependents + next_dependents
    for node in case.dependents:
        if not node.case.entry.home not in [node.case.entry.home
                                            for node in dependents]:
            create_testr_nested_suite(creator, node.case, suite, new_dependents,
                                      next_dependents = cast.dependents)
    return suite


class SubUnitLoader(object):

    def discover(self, start_dir, pattern='test*.py', top_level_dir=None):
        pass

    def getTestCaseNames(self, testCaseClass):
        pass

    def loadTestsFromModule(self, module, use_load_tests=True):
       pass

    def loadTestsFromName(self, name, module=None):
       pass

    def loadTestsFromNames(self, names, module=None):
       pass

    def loadTestsFromTestCase(self, testCaseClass):
       pass


class SubUnitInitiator(TestInitiator):

    def __init__(self, argv=None, stream=None):
        TestInitiator.__init__(self, argv=argv, show_plan_arg="--list")
        self.argv = argv
        self._show_best_proc_count = False
        self.stream = stream or sys.stdout

    def _create_test_suite(self):
        return create_testr_parallel_suite(self.plan)

    def discover_and_exit(self):
        self.run_and_exit()

    def _filter_command_line_arg(self, arg):
        if arg[:9] == "--idfile=":
            self.load_id_file(arg[9:])
            return True
        if arg == "--best-proc-count":
            self._show_best_proc_count = True
        return super(SubUnitInitiator, self)._filter_command_line_arg(arg)

    def load_id_file(self, id_file):
        with open(id_file) as file:
            for line in file:
                print(line)

    def run_and_exit(self):
        if self._arg_show_plan:
            self.show_plan()
        elif self._show_best_proc_count:
            self.show_best_proc_count()
        else:
            self.run_tests()

    def run_tests(self):
        from subunit.run import SubunitTestRunner
        runner = SubunitTestRunner(stream=self.stream)

        suite = self._create_test_suite()
        from subunit import TestProtocolClient
        from subunit.test_results import AutoTimingTestResultDecorator
        result = TestProtocolClient(self.stream)
        result = AutoTimingTestResultDecorator(result)
        #suite(result)  # <--- runs the tests

        result = runner.run(suite)


        #suite.run(result) #result.run(suite)

        # from subunit.run import SubunitTestRunner
        # from subunit.run import SubunitTestProgram
        # runner = SubunitTestRunner(stream=self.stream)
        # loader = SubUnitLoader()
        # SubunitTestProgram(
        #     module=None,
        #     argv=self.argv,
        #     suite=suite,
        #     testRunner=runner,
        #     testLoader=loader,
        #     stdout=sys.std  out)
        # print("\n\nMARIO: SUCCESS? %s" % result)
        # print("\n\nMARIO: SUCCESS? %s" % result.wasSuccessful())
        # print("\n\nMARIO: SUCCESS? %s" % result.testsRun)
        # print("\n\nMARIO: SUCCESS? %s" % suite)

        if not result.wasSuccessful():
            sys.exit(1)
        return result

    def show_best_proc_count(self):
        procs = ProcOrganizer(self.plan).procs
        print("best proc count = %d" % len(procs))
        sys.exit(0)


    def show_plan(self):
        """Prints information on test entries and the order they will run."""
        for case in self.cases:
            if case.entry.home is not None:
                self.stream.write('%s ' % case.entry.home.__name__)

