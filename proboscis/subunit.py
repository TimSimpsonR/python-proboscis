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



def should_run(case):
    return case.entry.info.enabled and case.entry.home is not None


def is_root_case(case):
    info = case.entry.info
    return not (info.depends_on or info.depends_on_groups)

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
    for case in plan.tests:
        info = case.entry.info
        if should_run(case) and is_root_case(case):
            suite = create_testr_nested_suite(creator, case)
            root_suite.addTest(suite)
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
        if not dependents:
            create_testr_nested_suite(creator, node.case, suite, new_dependents,
                                      next_dependents=case.dependents)
        elif not node.case.entry.home not in [node.case.entry.home
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
        self.stream = stream or sys.stdout

    def _create_test_suite(self):
        return create_testr_parallel_suite(self.plan)

    def discover_and_exit(self):
        self.run_and_exit()

    def _filter_command_line_arg(self, arg):
        if arg[:9] == "--idfile=":
            self.load_id_file(arg[9:])
            return True
        return super(SubUnitInitiator, self)._filter_command_line_arg(arg)

    def load_id_file(self, id_file):
        with open(id_file) as file:
            for line in file:
                print(line)

    def run_and_exit(self):
        if self._arg_show_plan:
            self.show_plan()
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

    def show_plan(self):
        """Prints information on test entries and the order they will run."""
        for case in self.cases:
            if case.entry.home is not None:
                self.stream.write('%s ' % case.entry.home.__name__)

