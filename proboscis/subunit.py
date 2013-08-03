"""
Proboscis Subunit / TestRepository Support
==========================================

Contains methods and classes to make a Proboscis test suite compatable with
Test Repository, subunit, and its friends.

This functionality is currently in Beta. It can currently only be used with a
subset of TestR's functionality.


Explanation
-----------

Because there is a philosophical impedance between Proboscis and TestR it is
difficult to translate the model of the former to the later.

There are two methods to achieve parallel execution using TestR:

1. Ask it to only run all tests which depend on each other in some way in the
   same process. This way nothing breaks, though the bottleneck becomes the
   slowest executing chain of tests.
2. Change every test which is a dependency to a test resource. I'm not sure
   yet how to handle "runs_after" situations where tests may check things
   are cleaned up. It's def. not a one-to-one mapping.

For now, this module attempts style #1.


Known issues
------------

* TestR chooses whether or not to run tests in parallel by deciding how long
  things seems to take. In theory, it will run as much in parallel as possible.
  However, you can double check by calling this script directly with the
  --best-proc-count argument, which will cause the number of processes, or
  "chains", to print out. Another way to trouble shoot things is to call
  the script with "--show-plan" which for subunit will list out all tests, in
  order, according to their individual process / chain.
* TestR will first call this script with "--list" at which point a "shallow"
  list, containing only the first test of each chain, will be returned. The
  idea is that this forces TestR to only parallelize the test list based on
  chains, allowing tests within a chain to still depend on each other within
  a process. However, when running, all test results are reported via stdout,
  giving TestR the knowledge of these tests. It may then pass back these tests
  within the chains if the "--failing" option is used. There is logic in place
  currently to filter by looking through all tests in a chain and if any match,
  to run the entire chain. In practice however this does not always work and
  the results of using the --failing option with TestR seem to be random.


Misc
----

The environment variable "FORCE_FORK" can be specified to "chain" to be created
using subunit's IsolatedTestSuite rather than a normal TestSuite; this causes
the process to fork when running. Note that this is not the same as running in
parallel, and is done simply to make tests run in an independent process in
case something crashes. It also gets in the way of Proboscis's ability to
skip dependent tests when their dependencies fail. This is mainly useful to
ensure chains can in fact operate in their own process and that their test's
dependencies have been fully specified.

"""
from __future__ import absolute_import

import os
import sys
import unittest

from subunit import IsolatedTestSuite
from subunit import TestProtocolClient
from subunit.test_results import AutoTimingTestResultDecorator
from subunit.run import SubunitTestRunner
from testtools import ExtendedToStreamDecorator

from proboscis.case import TestInitiator
from proboscis.case import TestResultListener
from proboscis.case import TestSuiteCreator



class ProcOrganizer(object):
    """
    Given a Proboscis TestPlan object, this iterates the tests and deduces all
    independent "chains", which are all tests that depend on each other and
    would need to run in the same process.
    """

    def __init__(self, plan):
        self.case_to_proc = {}
        self.procs = []
        index = 0
        cases = []
        for case in plan.tests:
            if should_run(case):
                case._order = index
                index += 1
                cases.append(case)
            else:
                case._order = None
        for case in cases:
            self._place_case(case)

    def _get_proc(self, case):
        proc = self.case_to_proc.get(case)
        if not proc:
            proc = set((case, ))
            self.procs.append(proc)
            self.case_to_proc[case] = proc
        return proc

    def _move_case_to_proc(self, case, proc):
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

    def _place_case(self, case):
        proc = self._get_proc(case)
        for dep in case.dependents:
            if (dep.case._order is not None):  # make sure it needs to run
                self._move_case_to_proc(dep.case, proc)



def should_run(case):
    """Returns true if a case actually does anything."""
    return case.entry.info.enabled and case.entry.home is not None


def case_in_filter(case, filters):
    """True if the case is refered to by one of the given subunit filters."""
    if hasattr(case.entry, 'home') and case.entry.home is not None:
        return case.entry.home.__name__ in filters
    else:
        return False


def any_case_in_filter(cases, filters):
    """True if any of the cases are referenced by the given subunit filters."""
    for case in cases:
        if case_in_filter(case, filters):
            return True
    return False


def create_testr_parallel_suite(plan, filters, force_fork):
    """
    Given a plan, creates a test suite which has only top level entries which
    are themselves suites. The idea is that each of these suites can then
    run in a seperate process as they are an independent chain of dependencies.
    """
    test_loader = unittest.TestLoader()
    root_suite = unittest.TestSuite()
    creator = TestSuiteCreator(test_loader)
    procs = ProcOrganizer(plan).procs
    for proc in procs:
        if force_fork:
            proc_suite = IsolatedTestSuite()
        else:
            proc_suite = unittest.TestSuite()
        cases = sorted(list(proc), key=lambda x : x._order)
        if not filters or any_case_in_filter(cases, filters):
            for case in cases:
                if should_run(case):
                    add_case_to_suite(creator, case, proc_suite)
            root_suite.addTest(proc_suite)
    return root_suite


def create_testr_list_suite(plan, test_loader=None):
    """
    Given a plan, creates a test suite which has only top level entries which
    are themselves suties. Unlike create_testr_parallel_suite though these
    suites only have a single entry. This is so the other tests will be hidden
    from TestRepository, forcing it to split up the load based on chains
    instead of tests.
    """
    test_loader = test_loader or unittest.TestLoader()
    creator = TestSuiteCreator(test_loader)
    root_suite = unittest.TestSuite()
    procs = ProcOrganizer(plan).procs
    for proc in procs:
        cases = sorted(list(proc), key=lambda x : x._order)
        if len(cases) > 0:
            proc_suite = unittest.TestSuite()
            add_case_to_suite(creator, cases[0], proc_suite)
            root_suite.addTest(proc_suite)
    return root_suite


def add_case_to_suite(creator, case, suite):
    """Translates a Proboscis TestCase into subunit test suites."""
    tests = creator.loadTestsFromTestEntry(case)
    for test in tests:
        suite.addTest(test)


class TestResult(TestResultListener, ExtendedToStreamDecorator):
    """
    Extension of subunit TestResult that works with TestRepository while also
    supporting Proboscis's ability to skip dependent tests when their
    dependencies fail.
    """

    def __init__(self, *args, **kwargs):
        TestResultListener.__init__(self, ExtendedToStreamDecorator)
        ExtendedToStreamDecorator.__init__(self, *args, **kwargs)


def subunit_replacement_run_method(self, test):
    """
    Replacement for SubunitTestRunner's run method which uses a TestResult
    class compatable both with Proboscis's dependent test skip mechanism and
    Subunit's reporting capabilities.
    """
    result = self._list(test)
    result = TestResult(result)
    result = AutoTimingTestResultDecorator(result)
    if self.failfast is not None:
        result.failfast = self.failfast
    result.startTestRun()
    try:
        test(result)
    finally:
        result.stopTestRun()
    return result


class SubunitInitiator(TestInitiator):
    """
    Pass control to this class from a script to execute tests using Subunit.
    """

    def __init__(self, argv=None, stream=None):
        self.filters = []
        self._force_fork = False
        self._show_best_proc_count = False
        self._list_for_testr = False
        TestInitiator.__init__(self, argv=argv)
        self._force_fork = os.environ.get("FORCE_FORK") is not None
        self.argv = argv
        self.stream = stream or sys.stdout

    def _create_test_suite(self):
        return create_testr_parallel_suite(self.plan, self.filters,
                                           self._force_fork)

    def discover_and_exit(self):
        self.run_and_exit()

    def _filter_command_line_arg(self, arg):
        if arg[:9] == "--idfile=":
            self.load_id_file(arg[9:])
            return True
        if arg == "--best-proc-count":
            self._show_best_proc_count = True
        if arg == "--failing":
            self._force_fork = True
        if arg == "--list":
            self._list_for_testr = True
        return super(SubunitInitiator, self)._filter_command_line_arg(arg)

    def _filter_command_line_args(self, argv):
        for index in range(len(argv) - 2):
            if argv[index + 1] == "--load-list":
                file_name = argv[index + 2]
                self._load_filter(file_name)

        return super(SubunitInitiator, self)._filter_command_line_args(argv)

    def list_for_testr(self):
        """Prints information on test entries and the order they will run."""
        runner = SubunitTestRunner(stream=self.stream)
        suite = create_testr_list_suite(self.plan)
        runner.list(suite)

    def _load_filter(self, file_name):
        with open(file_name) as f:
            self.filters.append(f.readline().strip())

    def load_id_file(self, id_file):
        with open(id_file) as file:
            for line in file:
                print(line)

    def run_and_exit(self):
        if self._arg_show_plan:
            self.show_plan()
        elif self._list_for_testr:
            self.list_for_testr()
        elif self._show_best_proc_count:
            self.show_best_proc_count()
        else:
            self.run_tests()

    def run_tests(self):
        from subunit.run import SubunitTestRunner
        runner = SubunitTestRunner(stream=self.stream)

        def new_run(*args, **kwargs):
            return subunit_replacement_run_method(runner, *args, **kwargs)

        runner.run = new_run
        suite = self._create_test_suite()
        from subunit import TestProtocolClient
        from subunit.test_results import AutoTimingTestResultDecorator
        result = runner.run(suite)
        if not result.wasSuccessful():
            sys.exit(1)
        return result

    def show_best_proc_count(self):
        procs = ProcOrganizer(self.plan).procs
        print("best proc count = %d" % len(procs))
        sys.exit(0)

    def show_plan(self):
        procs = ProcOrganizer(self.plan).procs
        for index, proc in enumerate(procs):
            print("CHAIN %d:" % index)
            for case in proc:
                print("\t%s" % case)
        sys.exit(0)


