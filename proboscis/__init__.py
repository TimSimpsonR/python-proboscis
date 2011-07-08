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

import os
import sys
import types
import unittest
from collections import deque
from nose import core
from nose import result
from nose.plugins.skip import SkipTest

from proboscis.decorators import decorate_class


class TestRegistry(object):
    """Stores test information."""
    def __init__(self):
        self.tests = []
        self.groups = {}
        self.classes = {}
        self.__has_been_sorted = False

    def ensure_group_exists(self, group_name):
        """Adds the group if it does not exist."""
        if not group_name in self.groups:
            self.groups[group_name] = TestGroup(group_name)

    def filter_test_list(self, group_names=None, classes=None, functions=None):
        """Whittles down test list to hose matching criteria."""
        if not self.__has_been_sorted:
            raise RuntimeError("Can't filter an unsorted list.")
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
            entry = self.tests.pop()
            if entry.contains(group_names, test_homes):
                filtered_list.append(entry)
                # Add any groups this depends on so they will run as well.
                for group_name in entry.info.depends_on_groups:
                    if not group_name in group_names:
                        group_names.append(group_name)
                for test_home in entry.info.depends_on:
                    if not test_home in test_homes:
                        test_homes.append(test_home)
        self.tests = list(reversed(filtered_list))

    def get_group(self, group_name):
        """Finds a group by name."""
        self.ensure_group_exists(group_name)
        return self.groups[group_name]

    def get_sorted_tests(self):
        """Sorts and returns the test list."""
        self.sort()
        return self.tests

    def register(self, cls=None, **kwargs):
        """Registers a test entry."""
        if self.__has_been_sorted:
            raise RuntimeError("New entries not allowed after call to sort.")
        info = TestCaseInfo(**kwargs)
        entry = TestEntry(cls, info)
        for group_name in info.groups:
            group = self.get_group(group_name)
            group.add_entry(entry)
        for group in info.depends_on_groups:
            self.ensure_group_exists(group)
        self.tests.append(entry)
        if cls:
            if not cls in self.classes:
                self.classes[cls] = []
            self.classes[cls].append(entry)
        return cls

    def sort(self):
        """Sorts all registered test entries."""
        if self.__has_been_sorted:
            return
        self.__has_been_sorted = True
        self.tests = TestGraph(self).sort()


class TestCaseInfo:
    """Represents metadata attached to a TestCase."""

    def __init__(self,
                 groups=None,
                 depends_on=None,
                 depends_on_classes=None,
                 depends_on_groups=None,
                 enabled=True,
                 never_skip=False):
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
        self.never_skip = never_skip

    def __repr__(self):
        return "TestCaseInfo(groups=" + str(self.groups) + \
               ", depends_on=" + str(self.depends_on) + \
               ", depends_on_groups=" + str(self.depends_on_groups) + \
               ", enabled=" + str(self.enabled) + ")"

    def __str__(self):
        return "groups = " + str(self.groups) + \
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
    """Represents a union of a TestCase and TestCaseInfo.

    This class is also used to store status information, such as the dependent
    TestEntry objects (discovered when this test is sorted) and any failure
    in the dependencies of this test (used to raise SkipTest if needed).

    """
    def __init__(self, home, info):
        self.home = home
        self.info = info
        self.dependents = []  # This is populated when we sort the tests.
        self.dependency_failure = None
        for dep in self.info.depends_on:
            if dep is self.home:
                raise RuntimeError("TestEntry depends on its own class:" +
                                   str(self))
        for dependency_group in self.info.depends_on_groups:
            for my_group in self.info.groups:
                if my_group == dependency_group:
                    raise RuntimeError("TestEntry depends on a group it " \
                                       "itself belongs to: " + str(self))

    def check_dependencies(self):
        """If a dependency has failed, SkipTest is raised."""
        if self.dependency_failure != None and self.dependency_failure != self\
           and not self.info.never_skip:
            raise SkipTest("Failure in " + str(self.dependency_failure.home))

    def contains(self, group_names, classes):
        """True if this belongs to any of the given groups or classes."""
        for group_name in group_names:
            if group_name in self.info.groups:
                return True
        for cls in classes:
            if cls == self.home:
                return True
        return False

    def fail_test(self, dependency_failure=None):
        """Called when this entry fails to notify dependents."""
        if not dependency_failure:
            dependency_failure = self
        if not self.dependency_failure:  # Do NOT overwrite the first cause
            self.dependency_failure = dependency_failure
            for dependent in self.dependents:
                dependent.fail_test(dependency_failure=dependency_failure)

    def __repr__(self):
        return "TestEntry(" + repr(self.home) + ", " + \
               repr(self.info) + ", " + object.__repr__(self) + ")"

    def __str__(self):
        return "Home = " + str(self.home) + ", Info(" + str(self.info) + ")"


class TestNode:
    """Representation of a TestEntry used in sorting."""
    def __init__(self, entry):
        self.entry = entry
        self.dependencies = []
        self.dependents = []

    def add_dependency(self, node):
        """Adds a bidirectional link between this node and a dependency.

        This also informs the dependency TestEntry of its dependent.  It is
        intuitive to specify dependencies when writing tests, so we have
        to wait until this phase to determine the dependents of the TestEntry.

        """
        # TODO: Could this be sped up by using a set?
        if node in self.dependencies:
            return
        self.dependencies.append(node)
        node.dependents.append(self)
        node.entry.dependents.append(self.entry)

    @property
    def has_no_dependencies(self):
        return len(self.dependencies) == 0

    def pop_dependent(self):
        """Removes and returns a dependent from this nodes dependent list.

        This act of destruction is one reason why this second representation
        of a TestEntry is necessary.

        """
        dependent = self.dependents.pop()
        dependent.dependencies.remove(self)
        return dependent


class TestGraph:
    """Used to sort the tests in a registry in the correct order.

    As it sorts, it also adds dependent information to the TestEntries, which
    means calling it twice messes stuff up.

    """

    def __init__(self, registry):
        self.nodes = []
        self.registry = registry
        for entry in registry.tests:
            self.nodes.append(TestNode(entry))
        for node in self.nodes:
            for dependency_group in node.entry.info.depends_on_groups:
                d_group_nodes = self.nodes_for_group(dependency_group)
                for dependency_group_node in d_group_nodes:
                    node.add_dependency(dependency_group_node)
            for dependency in node.entry.info.depends_on:
                d_nodes = self.nodes_for_class_or_function(dependency)
                for dependency_node in d_nodes:
                    node.add_dependency(dependency_node)

    def node_for_entry(self, entry):
        """Finds the node attached to the given entry."""
        for node in self.nodes:
            if node.entry is entry:
                return node
        raise RuntimeError("Could not find node for entry " + str(entry))

    def nodes_for_class_or_function(self, test_home):
        """Returns nodes attached to the given class."""
        return (n for n in self.nodes if n.entry.home is test_home)

    def nodes_for_group(self, group_name):
        """Returns nodes attached to the given group."""
        group = self.registry.groups[group_name]
        return (self.node_for_entry(entry) for entry in group.entries)

    def sort(self):
        """Returns a sorted list of entries.

        Dismantles this graph's list of nodes and adds dependent information
        to the list of TestEntries (iow don't call this twice).

        """
        independent_nodes = deque((n for n in self.nodes
                                   if n.has_no_dependencies))
        ordered_nodes = []  # The new list
        while independent_nodes:
            i_node = independent_nodes.popleft()
            ordered_nodes.append(i_node)
            while i_node.dependents:
                d_node = i_node.pop_dependent()
                if d_node.has_no_dependencies:
                    independent_nodes.appendleft(d_node)
        # Search for a cycle
        for node in self.nodes:
            if not node.has_no_dependencies:
                raise RuntimeError("Cycle found on node " + str(node.entry))
        return list((n.entry for n in ordered_nodes))


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
        if hasattr(test.test, "__proboscis_entry__"):
            entry = test.test.__proboscis_entry__
            entry.fail_test()


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

    def __init__(self, test_entry):
        _old_setup = None
        if hasattr(test_entry.home, 'setup'):  # Don't destroy nose-style setup
            _old_setup = test_entry.home.setup
        def cb_check(self=None):
            test_entry.check_dependencies()
            if _old_setup is not None:
                _old_setup()
        self.__proboscis_entry__ = test_entry
        unittest.FunctionTestCase.__init__(self, testFunc=test_entry.home,
                                           setUp=cb_check)


class TestSuiteCreator(object):
    """Turns Proboscis test entries into elements to be run by unittest."""

    def __init__(self, loader):
        self.loader = loader

    def loadTestsFromTestEntry(self, test_entry):
        """Wraps a test class in magic so it will skip on dependency failures.

        Decorates the testEntry class's setUp method to raise SkipTest if
        tests this test was dependent on failed or had errors.

        """
        if test_entry.home == None:
            return []
        if isinstance(test_entry.home, type):
            return self.wrap_class(test_entry)
        if isinstance(test_entry.home, types.FunctionType):
            return self.wrap_function(test_entry)

    def wrap_class(self, test_entry):
        def cb_check(self=None):
            test_entry.check_dependencies()
        testCaseClass = decorate_class(setUp_method=cb_check)(test_entry.home)
        testCaseNames = self.loader.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']
        suite = []
        if issubclass(test_entry.home, unittest.TestCase):
            for name in testCaseNames:
                test_instance = testCaseClass(name)
                setattr(test_instance, "__proboscis_entry__", test_entry)
                suite.append(test_instance)
        else:
            raise RuntimeError("can't yet wrap test classes of type " +
                               str(test_entry.home) + ".")
        return suite

    def wrap_function(self, test_entry):
        return [FunctionTest(test_entry)]


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
                 argv=sys.argv,
                 *args, **kwargs):
        classes = classes or []
        groups = groups or []
        argv = self.extract_groups_from_argv(argv, groups)
        if "suite" in kwargs:
            raise ValueError("'suite' is not a valid argument, as Proboscis " \
                             "creates the suite.")

        self.__loader = testLoader or unittest.TestLoader()

        if env is None:
            env = os.environ
        if config is None:
            config = self.makeConfig(env, plugins)

        if testRunner is None:
            runner_cls = test_runner_cls(core.TextTestRunner,
                                         "ProboscisTestRunner")
            testRunner = runner_cls(config.stream,
                                    verbosity=3,  # config.verbosity,
                                    config=config)
        registry.sort()
        if len(groups) > 0:
            registry.filter_test_list(group_names=groups)
        self.entries = registry.get_sorted_tests()
        if "--show-plan" in argv:
            self.show_plan()
            return
        else:
            self.__suite = self.create_test_suite_from_entries(config,
                                                               self.entries)            
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
            self.call_nose = run

    def create_test_suite_from_entries(self, config, entries):
        from nose.suite import ContextSuiteFactory
        creator = TestSuiteCreator(self.__loader)
        suite = ContextSuiteFactory(config)([])
        for entry in entries:
            if entry.info.enabled and entry.home != None:
                tests = creator.loadTestsFromTestEntry(entry)
                for test in tests:
                    suite.addTest(test)        
        return suite

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
        self.call_nose()

    def show_plan(self):
        """Prints information on test entries and the order they will run."""
        import pydoc
        print("   *  *  *  Test Plan  *  *  *")
        for entry in self.entries:
            print(entry.home)
            doc = pydoc.getdoc(entry.home)
            if doc:
                print(doc)
            for field in str(entry.info).split(', '):
                print("\t" + field)
    
    @property
    def test_suite(self):
        return self.__suite
