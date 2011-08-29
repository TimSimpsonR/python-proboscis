# Copyright (c) 2011 Rackspace
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Creates TestCases from a list of TestEntries."""
from functools import wraps

import types
import unittest

from collections import deque
from nose import result
from nose.plugins.skip import SkipTest
from proboscis import TestMethodClassEntry

from proboscis.decorators import decorate_class
from proboscis.sorting import TestGraph

class TestPlan(object):
    """Grabs information from the TestRegistry and creates a test plan."""

    def __init__(self, groups, test_entries):
        graph = self._create_graph(groups, test_entries)
        self.tests = graph.sort()

    @staticmethod
    def _create_graph(groups, test_entries):
        tests = []
        entries = {}
        for entry in test_entries:
            test_cases = TestPlan._create_test_cases_for_entry(entry)
            entries[entry] = test_cases
            tests += test_cases
        return TestGraph(groups, entries, tests)

    @staticmethod
    def _create_test_cases_for_entry(entry):
        """Processes a test case entry."""
        if not hasattr(entry, 'children'):
            return [TestCase(entry)]
        #TODO: If its a factory, make more than one state, and for each one
        # create new TestCase instances for all the entries.
        state = TestMethodState(entry)
        return [TestCase(child_entry, state=state)
                for child_entry in entry.children]

    def create_test_suite(self, config, loader):
        """Transforms the plan into a Nose test suite."""
        from nose.suite import ContextSuiteFactory
        creator = TestSuiteCreator(loader)
        suite = ContextSuiteFactory(config)([])
        for case in self.tests:
            print("GET READY FOR CASE!")
            print(case.entry.info.enabled)
            print(case.entry.home)
            print()
            if case.entry.info.enabled and case.entry.home is not None:
                tests = creator.loadTestsFromTestEntry(case)
                for test in tests:
                    suite.addTest(test)
        return suite

    def filter(self, group_names=None, classes=None, functions=None):
        """Whittles down test list to hose matching criteria."""
        test_homes = []
        classes = classes or []
        functions = functions or []
        for cls in classes:
            test_homes.append(cls)
        for function in functions:
            test_homes.append(function)
        group_names = group_names or []
        filtered_list = []
        while self.tests:
            case = self.tests.pop()
            if case.entry.contains(group_names, test_homes):
                filtered_list.append(case)
                # Add any groups this depends on so they will run as well.
                for group_name in case.entry.info.depends_on_groups:
                    if not group_name in group_names:
                        group_names.append(group_name)
                for test_home in case.entry.info.depends_on:
                    if not test_home in test_homes:
                        test_homes.append(test_home)
        self.tests = list(reversed(filtered_list))


class TestCase(object):
    """Represents an instance of a TestEntry.

    This class is also used to store status information, such as the dependent
    TestEntry objects (discovered when this test is sorted) and any failure
    in the dependencies of this test (used to raise SkipTest if needed).

    There may be multiple TestCase instances for each TestEntry instance.

    """
    def __init__(self, entry, state=None):
        self.entry = entry
        self.dependents = []  # This is populated when we sort the tests.
        self.dependency_failure = None
        self.state = state

    def check_dependencies(self):
        """If a dependency has failed, SkipTest is raised."""
        if self.dependency_failure is not None and \
           self.dependency_failure != self and not self.entry.info.always_run:
            home = self.dependency_failure.entry.home
            raise SkipTest("Failure in %s" % home)

    def fail_test(self, dependency_failure=None):
        """Called when this entry fails to notify dependents."""
        if not dependency_failure:
            dependency_failure = self
        if not self.dependency_failure:  # Do NOT overwrite the first cause
            self.dependency_failure = dependency_failure
            for dependent in self.dependents:
                dependent.fail_test(dependency_failure=dependency_failure)

    def __repr__(self):
        return "TestCase(" + repr(self.entry.home) + ", " + \
               repr(self.entry.info) + ", " + object.__repr__(self) + ")"

    def __str__(self):
        return "Home = " + str(self.entry.home) + ", Info(" + \
               str(self.entry.info) + ")"


class TestResultListener():
    """Implements methods of TestResult to be informed of test failures."""

    def __init__(self, chain_to_cls):
        self.chain_to_cls = chain_to_cls

    def addError(self, test, err):
        self.onError(test)
        self.chain_to_cls.addError(self, test, err)

    def addFailure(self, test, err):
        self.onError(test)
        self.chain_to_cls.addFailure(self, test, err)

    def onError(self, test):
        """Notify a test entry and its dependents of failure."""
        if hasattr(test.test, "__proboscis_case__"):
            case = test.test.__proboscis_case__
            case.fail_test()



class TestResult(TestResultListener, result.TextTestResult):
    """Mixes TestResultListener with nose's TextTestResult class."""

    # I had issues extending TextTestResult directly so resorted to this.

    def __init__(self, stream, descriptions, verbosity, config=None,
                 errorClasses=None):
        TestResultListener.__init__(self, result.TextTestResult)
        result.TextTestResult.__init__(self, stream, descriptions, verbosity,
                                       config, errorClasses)


def test_runner_cls(wrapped_cls, cls_name):
    """Creates a test runner class which uses Proboscis TestResult."""
    new_dict = wrapped_cls.__dict__.copy()

    def cb_make_result(self):
        return TestResult(self.stream, self.descriptions, self.verbosity)
    new_dict["_makeResult"] = cb_make_result
    return type(cls_name, (wrapped_cls,), new_dict)



class FunctionTest(unittest.FunctionTestCase):
    """Wraps a single function as a test runnable by unittest / nose."""

    def __init__(self, test_case):
        func = test_case.entry.home
        _old_setup = None
        if hasattr(func, 'setup'):  # Don't destroy nose-style setup
            _old_setup = func.setup
        def cb_check(self=None):
            test_case.check_dependencies()
            if _old_setup is not None:
                _old_setup()
        self.__proboscis_case__ = test_case
        unittest.FunctionTestCase.__init__(self, testFunc=func, setUp=cb_check)


class TestMethodState(object):
    """Manages a test class instance used by one or more test methods."""

    def __init__(self, entry):
        self.entry = entry
        assert isinstance(self.entry, TestMethodClassEntry)
        self.instance = None

    def get_state(self):
        if not self.instance:
            self.instance = self.entry.home()
        return self.instance


class MethodTest(unittest.FunctionTestCase):
    """Wraps a method as a test runnable by unittest."""

    def __init__(self, test_case):
        assert test_case.state is not None
        #TODO: Figure out how to attach calls to BeforeMethod and BeforeClass,
        #      AfterMethod and AfterClass. It should be easy enough to
        #      just find them using the TestEntry parent off test_case Entrty.
        def cb_check(self=None):
            test_case.check_dependencies()
        @wraps(test_case.entry.home)
        def func(self=None):  # Called by FunctionTestCase
            unbound_method = test_case.entry.home
            unbound_method(test_case.state.get_state())
        self.__proboscis_case__ = test_case
        unittest.FunctionTestCase.__init__(self, testFunc=func, setUp=cb_check)


class TestSuiteCreator(object):
    """Turns Proboscis test cases into elements to be run by unittest."""

    def __init__(self, loader):
        self.loader = loader

    def loadTestsFromTestEntry(self, test_case):
        """Wraps a test class in magic so it will skip on dependency failures.

        Decorates the testEntry class's setUp method to raise SkipTest if
        tests this test was dependent on failed or had errors.

        """
        home = test_case.entry.home
        if home is None:
            return []
        if isinstance(home, types.MethodType):
            return self.wrap_method(test_case)
        if isinstance(home, type):
            return self.wrap_unittest_test_case_class(test_case)
        if isinstance(home, types.FunctionType):
            return self.wrap_function(test_case)
        raise RuntimeError("Unknown test type:" + str(type(home)))

    def wrap_function(self, test_case):
        return [FunctionTest(test_case)]

    def wrap_method(self, test_case):
        return [MethodTest(test_case)]

    def wrap_unittest_test_case_class(self, test_case):
        original_cls = test_case.entry.home
        def cb_check(self=None):
            test_case.check_dependencies()
        testCaseClass = decorate_class(setUp_method=cb_check)(original_cls)
        testCaseNames = self.loader.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']
        suite = []
        if issubclass(original_cls, unittest.TestCase):
            for name in testCaseNames:
                test_instance = testCaseClass(name)
                setattr(test_instance, "__proboscis_case__", test_case)
                suite.append(test_instance)
        #else:
        #    raise RuntimeError("can't yet wrap test classes of type " +
        #                       str(test_entry.home) + ".")
        return suite
