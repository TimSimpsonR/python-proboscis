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

"""Extension for Nose to facilitate higher level testing.

Changes how tests are discovered by forcing them to use a common decorator
which contains useful metadata such as whether or not they have dependencies
on other tests.  This allows larger processes or stories to be modelled and
run as tests.  Much of this functionality was "inspired" by TestNG.

"""

import inspect
import os
import pydoc
import sys
import types
import unittest
from nose import core

# This is here so Proboscis own test harness can change it while still calling
# TestProgram normally. Its how the examples are tested.
_override_default_stream=None

_default_argv=sys.argv


class TestEntryInfo:
    """Represents metadata attached to a TestCase."""

    def __init__(self,
                 groups=None,
                 depends_on=None,
                 depends_on_classes=None,
                 depends_on_groups=None,
                 enabled=True,
                 always_run=False):
        groups = groups or []
        depends_on = depends_on or []
        depends_on_classes = depends_on_classes or []
        for cls in depends_on_classes:
            depends_on.append(cls)
        depends_on_groups = depends_on_groups or []
        self.groups = groups
        self.depends_on = depends_on
        self.depends_on_groups = depends_on_groups
        self.enabled = enabled
        self.always_run = always_run
        self.inherit_groups=False

    def inherit(self, parent_entry):
        """The main use case is a method inheriting from a class decorator."""
        for group in parent_entry.groups:
            if group not in self.groups:
                self.groups.append(group)
        for item in parent_entry.depends_on_groups:
            if item not in self.depends_on_groups:
                self.depends_on_groups.append(item)
        for item in parent_entry.depends_on:
            if item not in self.depends_on:
                self.depends_on.append(item)
        if parent_entry.always_run:
            self.always_run = True
        #TODO: Determine how this should work.

    def __repr__(self):
        return "TestEntryInfo(groups=" + str(self.groups) + \
               ", depends_on=" + str(self.depends_on) + \
               ", depends_on_groups=" + str(self.depends_on_groups) + \
               ", enabled=" + str(self.enabled) + ")"

    def __str__(self):
        return "groups = [" + ",".join(self.groups) + ']' \
               ", enabled = " + str(self.enabled) + \
               ", depends_on_groups = " + str(self.depends_on_groups) + \
               ", depends_on = " + str(self.depends_on)


class TestGroup(object):
    """Represents a group of tests.

    Think of test groups as tags on a blog.  A test case may belong to multiple
    groups, and one group may have multiple test cases.

    """
    def __init__(self, name):
        self.name = name
        self.entries = []
        self.dependencies = []  # TODO: Is this needed?

    def add_entry(self, entry):
        """Adds a TestEntry to this group."""
        self.entries.append(entry)


class TestEntry(object):
    """Represents a function, method, or unittest.TestCase and its info."""

    def __init__(self, home_im_class, home, info):
        self.home_im_class = home_im_class
        self.home = home
        self.info = info
        for dep in self.info.depends_on:
            if dep is self.home:
                raise RuntimeError("TestEntry depends on its own class:" +
                                   str(self))
        for dependency_group in self.info.depends_on_groups:
            for my_group in self.info.groups:
                if my_group == dependency_group:
                    raise RuntimeError("TestEntry depends on a group it " \
                                       "itself belongs to: " + str(self))

    def contains(self, group_names, classes):
        """True if this belongs to any of the given groups or classes."""
        for group_name in group_names:
            if group_name in self.info.groups:
                return True
        for cls in classes:
            if cls == self.home:
                return True
        return False

    def write_doc(self, file):
        file.write(str(self.home) + "\n")
        doc = pydoc.getdoc(self.home)
        if doc:
            file.write(doc + "\n")
        for field in str(self.info).split(', '):
            file.write("\t" + field + "\n")

    def __repr__(self):
        return "TestEntry(" + repr(self.home) + ", " + \
               repr(self.info) + ", " + object.__repr__(self) + ")"

    def __str__(self):
        return "Home = " + str(self.home) + ", Info(" + str(self.info) + ")"


class TestMethodClassEntry(TestEntry):
    """A special kind of entry which references a class and a list of entries.

    The class is the class which owns the test methods, and the entries are
    the entries for those methods.

    """

    def __init__(self, home, info, children):
        super(TestMethodClassEntry, self).__init__(None, home, info)
        self.children = children

    def contains(self, group_names, classes):
        """True if this belongs to any of the given groups or classes."""
        if super(TestMethodClassEntry, self).contains(group_names, classes):
            return True
        for entry in children:
            if entry.contains(group_names, classes):
                return True
        return False




from proboscis.case import TestPlan
from proboscis.case import test_runner_cls

class TestRegistry(object):
    """Stores test information."""
    def __init__(self):
        self.reset()

    def ensure_group_exists(self, group_name):
        """Adds the group if it does not exist."""
        if not group_name in self.groups:
            self.groups[group_name] = TestGroup(group_name)

#    def filter_test_list(self, group_names=None, classes=None, functions=None):
#        """Whittles down test list to hose matching criteria."""
#        if not self.__has_been_sorted:
#            raise RuntimeError("Can't filter an unsorted list.")
#        test_homes = []
#        classes = classes or []
#        functions = functions or []
#        for cls in classes:
#            test_homes.append(cls)
#        for function in functions:
#            test_homes.append(function)
#        group_names = group_names or []
#        filtered_list = []
#        while self.tests:
#            entry = self.tests.pop()
#            if entry.contains(group_names, test_homes):
#                filtered_list.append(entry)
#                # Add any groups this depends on so they will run as well.
#                for group_name in entry.info.depends_on_groups:
#                    if not group_name in group_names:
#                        group_names.append(group_name)
#                for test_home in entry.info.depends_on:
#                    if not test_home in test_homes:
#                        test_homes.append(test_home)
#        self.tests = list(reversed(filtered_list))

    def get_group(self, group_name):
        """Finds a group by name."""
        self.ensure_group_exists(group_name)
        return self.groups[group_name]

    def get_test_plan(self):
        """Returns a sorted TestPlan that can be filtered."""
        return TestPlan(self.groups, self.tests)

#    def get_sorted_tests(self):
#        """Sorts and returns the test list."""
#        return TestGraph(TestRunner(self))
#        self.sort()
#        return self.tests

    def _mark_with_metadata(self, function, info):
        """Attaches info to a function for later reading.

        Because the decorated method is not yet seen as connected to the class
        all we can do is add the info to it and inspect it later.

        """
        function._proboscis_info_=info
        return function

    def register(self, test_home=None, **kwargs):
#        if self.__has_been_sorted:
#            raise RuntimeError("New entries not allowed after call to sort.")
        info = TestEntryInfo(**kwargs)
        if isinstance(test_home, types.FunctionType):
            return self._mark_with_metadata(test_home, info)
        elif test_home is None or issubclass(test_home, unittest.TestCase):
            return self.register_unittest_test_case(test_home, info)
        else:
            return self._register_test_class(test_home, info)

    def register_unittest_test_case(self, test_cls, info):
        entry = self._register_new_entry(None, test_cls, info)
        self.tests.append(entry)
        return entry.home

    def register_func(self, func, **kwargs):
#        if self.__has_been_sorted:
#            raise RuntimeError("New entries not allowed after call to sort.")
        info = TestEntryInfo(**kwargs)
        if not isinstance(func, types.FunctionType):
            raise RuntimeError("Expected a function.")
        entry = self._register_new_entry(None, func, info)
        self.tests.append(entry)
        return entry.home

    def _register_method(self, method, cls_info):
        cls = method.im_class
        #func = method.im_func
        method_info = method._proboscis_info_
        method_info.inherit(cls_info)
        entry = self._register_new_entry(cls, method, method_info)
        return entry

    def _register_new_entry(self, test_im_class, test_home, info):
        """Registers a unitttest style test entry."""
        entry = TestEntry(test_im_class, test_home, info)
        for group_name in info.groups:
            group = self.get_group(group_name)
            group.add_entry(entry)
        for group in info.depends_on_groups:
            self.ensure_group_exists(group)
        #self.tests.append(entry)
        if test_home:
            if not test_home in self.classes:
                self.classes[test_home] = []
            self.classes[test_home].append(entry)
        return entry

    def _register_test_class(self, cls, info):
        """Registers the methods within a class."""
        test_entries = []
        members = inspect.getmembers(cls, inspect.ismethod)
        for member in members:
            method = member[1]
            if hasattr(method, 'im_func'):
                func = method.im_func
                if hasattr(func, "_proboscis_info_"):
                    entry = self._register_method(method, info)
                    test_entries.append(entry)
        entry = TestMethodClassEntry(cls, info, test_entries)
        self.tests.append(entry)
        return entry.home


    def reset(self):
        """Wipes the registry."""
        self.tests = []
        self.groups = {}
        self.classes = {}
#        self.__has_been_sorted = False

#    def sort(self):
#        """Sorts all registered test entries."""
#        if self.__has_been_sorted:
#            return
#        self.__has_been_sorted = True
#        self.tests = TestGraph(self).sort()

#class TestCase(object):
#    """Represents a union of a TestCase and TestEntryInfo.
#
#    This class is also used to store status information, such as the dependent
#    TestEntry objects (discovered when this test is sorted) and any failure
#    in the dependencies of this test (used to raise SkipTest if needed).
#
#    """
#    def __init__(self, home, info):
#        self.home = home
#        self.home_cls = None  # Only set for bound methods
#        self.info = info
#        self.dependents = []  # This is populated when we sort the tests.
#        self.dependency_failure = None
#        for dep in self.info.depends_on:
#            if dep is self.home:
#                raise RuntimeError("TestEntry depends on its own class:" +
#                                   str(self))
#        for dependency_group in self.info.depends_on_groups:
#            for my_group in self.info.groups:
#                if my_group == dependency_group:
#                    raise RuntimeError("TestEntry depends on a group it " \
#                                       "itself belongs to: " + str(self))
#
#    def check_dependencies(self):
#        """If a dependency has failed, SkipTest is raised."""
#        if self.dependency_failure != None and self.dependency_failure != self\
#           and not self.info.always_run:
#            raise SkipTest("Failure in " + str(self.dependency_failure.home))
#
#    def contains(self, group_names, classes):
#        """True if this belongs to any of the given groups or classes."""
#        for group_name in group_names:
#            if group_name in self.info.groups:
#                return True
#        for cls in classes:
#            if cls == self.home:
#                return True
#        return False
#
#    def fail_test(self, dependency_failure=None):
#        """Called when this entry fails to notify dependents."""
#        if not dependency_failure:
#            dependency_failure = self
#        if not self.dependency_failure:  # Do NOT overwrite the first cause
#            self.dependency_failure = dependency_failure
#            for dependent in self.dependents:
#                dependent.fail_test(dependency_failure=dependency_failure)
#
#    def write_doc(self, file):
#        file.write(str(self.home) + "\n")
#        doc = pydoc.getdoc(self.home)
#        if doc:
#            file.write(doc + "\n")
#        for field in str(self.info).split(', '):
#            file.write("\t" + field + "\n")
#
#    def __repr__(self):
#        return "TestEntry(" + repr(self.home) + ", " + \
#               repr(self.info) + ", " + object.__repr__(self) + ")"
#
#    def __str__(self):
#        return "Home = " + str(self.home) + ", Info(" + str(self.info) + ")"
#



default_registry = TestRegistry()

def register(**kwargs):
    """Registers a test in proboscis's default registry."""
    default_registry.register(**kwargs)


def test(home=None, **kwargs):
    """Put this on a test class to cause Proboscis to run it. """
    if home:
        return default_registry.register(home)
    else:
        def cb_method(home_2):
            return default_registry.register(home_2, **kwargs)
        return cb_method


def test_func(home=None, **kwargs):
    """Put this on a free-standing function to register it correctly."""
    if home:
        return default_registry.register_func(home)
    else:
        def cb_method(home_2):
            return default_registry.register_func(home_2, **kwargs)
        return cb_method


#def before_class(home):
#    home._before_class = True

#class TestResultListener():
#    """Implements methods of TestResult to be informed of test failures."""
#
#    def __init__(self, chain_to_cls):
#        self.chain_to_cls = chain_to_cls
#
#    def addError(self, test, err):
#        self.onError(test)
#        self.chain_to_cls.addError(self, test, err)
#
#    def addFailure(self, test, err):
#        self.onError(test)
#        self.chain_to_cls.addFailure(self, test, err)
#
#    def onError(self, test):
#        """Notify a test entry and its dependents of failure."""
#        if hasattr(test.test, "__proboscis_entry__"):
#            entry = test.test.__proboscis_entry__
#            entry.fail_test()

#
#class TestResult(TestResultListener, result.TextTestResult):
#    """Mixes TestResultListener with nose's TextTestResult class."""
#
#    # I had issues extending TextTestResult directly so resorted to this.
#
#    def __init__(self, stream, descriptions, verbosity, config=None,
#                 errorClasses=None):
#        TestResultListener.__init__(self, result.TextTestResult)
#        result.TextTestResult.__init__(self, stream, descriptions, verbosity,
#                                       config, errorClasses)


#def test_runner_cls(wrapped_cls, cls_name):
#    """Creates a test runner class which uses Proboscis TestResult."""
#    new_dict = wrapped_cls.__dict__.copy()
#
#    def cb_make_result(self):
#        return TestResult(self.stream, self.descriptions, self.verbosity)
#    new_dict["_makeResult"] = cb_make_result
#    return type(cls_name, (wrapped_cls,), new_dict)


#
#class FunctionTest(unittest.FunctionTestCase):
#    """Wraps a single function as a test runnable by unittest / nose."""
#
#    def __init__(self, test_entry):
#        _old_setup = None
#        if hasattr(test_entry.home, 'setup'):  # Don't destroy nose-style setup
#            _old_setup = test_entry.home.setup
#        def cb_check(self=None):
#            test_entry.check_dependencies()
#            if _old_setup is not None:
#                _old_setup()
#        self.__proboscis_entry__ = test_entry
#        unittest.FunctionTestCase.__init__(self, testFunc=test_entry.home,
#                                           setUp=cb_check)
#
#
#class TestNgStyleMethodTest(unittest.FunctionTestCase):
#    """Wraps a method which is associated to a non-unique instance."""
#
#    def __init__(self, instance, test_entry):
#        _old_setup = None
#        if hasattr(test_entry.home, 'setup'):  # Don't destroy nose-style setup
#            _old_setup = test_entry.home.setup
#        def cb_check(self=None):
#            test_entry.check_dependencies()
#            if _old_setup is not None:
#                _old_setup()
#        self.__proboscis_entry__ = test_entry
#        unittest.FunctionTestCase.__init__(self, testFunc=test_entry.home,
#                                           setUp=cb_check)
#
#
#class TestSuiteCreator(object):
#    """Turns Proboscis test entries into elements to be run by unittest."""
#
#    def __init__(self, loader):
#        self.loader = loader
#
#    def loadTestsFromTestEntry(self, test_entry):
#        """Wraps a test class in magic so it will skip on dependency failures.
#
#        Decorates the testEntry class's setUp method to raise SkipTest if
#        tests this test was dependent on failed or had errors.
#
#        """
#        if test_entry.home is None:
#            return []
#        if isinstance(test_entry.home, type):
#            return self.wrap_class(test_entry)
#        if isinstance(test_entry.home, types.FunctionType):
#            return self.wrap_function(test_entry)
#        raise RuntimeError("Unknown test type:" + str(type(test_entry.home)))
#
#    def wrap_class(self, test_entry):
#        def cb_check(self=None):
#            test_entry.check_dependencies()
#        testCaseClass = decorate_class(setUp_method=cb_check)(test_entry.home)
#        testCaseNames = self.loader.getTestCaseNames(testCaseClass)
#        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
#            testCaseNames = ['runTest']
#        suite = []
#        if issubclass(test_entry.home, unittest.TestCase):
#            for name in testCaseNames:
#                test_instance = testCaseClass(name)
#                setattr(test_instance, "__proboscis_entry__", test_entry)
#                suite.append(test_instance)
#        #else:
#        #    raise RuntimeError("can't yet wrap test classes of type " +
#        #                       str(test_entry.home) + ".")
#        return suite
#
#    def wrap_function(self, test_entry):
#        if test_entry.home_cls:
#            raise RuntimeError("HOME " + str(test_entry.home))
#        return [FunctionTest(test_entry)]
#

class TestProgram(core.TestProgram):
    """The entry point of Proboscis.

    Creates the test suite and loaders before handing things off to Nose which
    runs as usual.

    """
    def __init__(self,
                 registry=default_registry,
                 classes=None,
                 groups=None,
                 testLoader=None,
                 config=None,
                 plugins=None,
                 env=None,
                 testRunner=None,
                 stream=None,
                 argv=None,
                 *args, **kwargs):
        classes = classes or []
        groups = groups or []
        argv = argv or sys.argv #_default_argv
        argv = self.extract_groups_from_argv(argv, groups)
        if "suite" in kwargs:
            raise ValueError("'suite' is not a valid argument, as Proboscis " \
                             "creates the suite.")

        self.__loader = testLoader or unittest.TestLoader()

        if _override_default_stream:
            stream = _override_default_stream

        if env is None:
            env = os.environ
        if config is None:
            config = self.makeConfig(env, plugins)
            if not stream:
                stream = config.stream

        stream = stream or sys.stdout
        
        if testRunner is None:
            runner_cls = test_runner_cls(core.TextTestRunner,
                                         "ProboscisTestRunner")
            testRunner = runner_cls(stream,
                                    verbosity=3,  # config.verbosity,
                                    config=config)
        #registry.sort()
        self.plan = registry.get_test_plan()
        
        if len(groups) > 0:
            self.plan.filter(group_names=groups)
        cases = self.plan.tests
        #self.entries = registry.get_sorted_tests()
        if "--show-plan" in argv:
            self.__run = self.show_plan
        else:
            self.__suite = self.create_test_suite_from_entries(config,
                                                               cases)
            def run():
                core.TestProgram.__init__(
                    self,
                    suite=self.__suite,
                    config=config,
                    env=env,
                    plugins=plugins,
                    testLoader=testLoader,  # Pass arg, not what we create
                    testRunner=testRunner,
                    argv=argv,
                    *args, **kwargs
                )
            self.__run = run

    def create_test_suite_from_entries(self, config, cases):
        return self.plan.create_test_suite(config, self.__loader)

    def extract_groups_from_argv(self, argv, groups):
        """Find the group argument if it exists and extract it.

        Nose will fail if we pass it an argument it doesn't know of, so this
        function modifies argv.

        """
        new_argv = [argv[0]]
        for arg in argv[1:]:
            if arg[:8] == "--group=":
                groups.append(arg[8:])
            else:
                new_argv.append(arg)
        return new_argv

    def run_and_exit(self):
        self.__run()

    def show_plan(self):
        """Prints information on test entries and the order they will run."""
        print("   *  *  *  Test Plan  *  *  *")
        for entry in self.entries:
            entry.write_doc(sys.stdout)
    
    @property
    def test_suite(self):
        return self.__suite
