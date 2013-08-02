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
    test_loader = test_loader or unittest.TestLoader()
    root_suite = root_suite or unittest.TestSuite()
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


def create_testr_nested_suite(creator, case, suite=None, dependents=None):
    suite = suite or unittest.TestSuite()
    add_case_to_suite(creator, case, suite)
    for node in case.dependents:
        if not dependents:
            create_testr_nested_suite(creator, node.case, suite, case.dependents)
        elif node.case.entry.home not in [node.case.entry.home for node in dependents]:  # Avoid double iteration.
            new_dependents = dependents + case.dependents
            #create_testr_nested_suite(creator, node.case, suite, new_dependents)
    return suite


class SubUnitInitiator(TestInitiator):

    def __init__(self, argv=None, stream=None):
        TestInitiator.__init__(self, argv=argv, show_plan_arg="--list")
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
        suite = self._create_test_suite()
        from subunit import TestProtocolClient
        from subunit.test_results import AutoTimingTestResultDecorator
        result = TestProtocolClient(self.stream)
        result = AutoTimingTestResultDecorator(result)
        suite(result)  # <--- runs the tests
        return result

    def show_plan(self):
        """Prints information on test entries and the order they will run."""
        for case in self.cases:
            if case.entry.home is not None:
                self.stream.write('%s ' % case.entry.home.__name__)

