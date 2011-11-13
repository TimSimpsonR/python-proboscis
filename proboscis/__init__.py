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
import sys
import types
import unittest


from proboscis import dependencies


# This is here so Proboscis own test harness can change it while still calling
# TestProgram normally. Its how the examples are tested.
OVERRIDE_DEFAULT_STREAM = None


if dependencies.use_nose:
    from nose import SkipTest
else:
    class SkipTest(Exception):
        def __init__(self, message):
            super(SkipTest, self).__init__(self, message)
            self.message = message

        def __str__(self):
            return self.message


class ProboscisTestMethodClassNotDecorated(Exception):
    """
    
    This denotes a very common error that seems somewhat unavoidable due to
    the fact it isn't possible to know if a method is bound or not in Python
    when you decorate it.
    
    """

    def __init__(self):
        super(Exception, self).__init__(self,
            "Proboscis attempted to run what looks like a bound method "
            "requiring a self argument as a free-standing function. Did you "
            "forget to put a @test decorator on the method's class?")



class TestGroup(object):
    """Represents a group of tests.

    Think of test groups as tags on a blog.  A test case may belong to multiple
    groups, and one group may have multiple test cases.

    """
    def __init__(self, name):
        self.name = name
        self.entries = []

    def add_entry(self, entry):
        """Adds a TestEntry to this group."""
        self.entries.append(entry)


def transform_depends_on_target(target):
    if isinstance(target, types.MethodType):
        return target.im_func
    else:
        return target


class TestEntryInfo:
    """Represents metadata attached to some kind of test code."""

    def __init__(self,
                 groups=None,
                 depends_on=None,
                 depends_on_classes=None,
                 depends_on_groups=None,
                 enabled=True,
                 always_run=False,
                 run_before_class=False,
                 run_after_class=False):
        groups = groups or []
        depends_on_list = depends_on or []
        depends_on_classes = depends_on_classes or []
        depends_on_groups = depends_on_groups or []
        self.groups = groups
        self.depends_on = set(transform_depends_on_target(target)
                              for target in depends_on_list)
        for cls in depends_on_classes:
            self.depends_on.add(cls)
        self.depends_on_groups = depends_on_groups
        self.enabled = enabled
        self.always_run = always_run
        self.inherit_groups = False
        self.before_class = run_before_class
        self.after_class = run_after_class

        if run_before_class and run_after_class:
            raise RuntimeError("It is illegal to set 'before_class' and "
                               "'after_class' to True.")

    def inherit(self, parent_entry):
        """The main use case is a method inheriting from a class decorator.

        Returns the groups this entry was added to.

        """
        added_groups = []
        for group in parent_entry.groups:
            if group not in self.groups:
                self.groups.append(group)
                added_groups.append(group)
        for item in parent_entry.depends_on_groups:
            if item not in self.depends_on_groups:
                self.depends_on_groups.append(item)
        for item in parent_entry.depends_on:
            if item not in self.depends_on:
                self.depends_on.add(item)
        if parent_entry.always_run:
            self.always_run = True
        return added_groups

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



class TestEntry(object):
    """Represents a function, method, or unittest.TestCase and its info."""

    def __init__(self, home, info):
        self.home = home
        self.homes = set([home])
        self.info = info
        self.__method = None
        self.__used_by_factory = False
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
        if hasattr(self, 'parent'):
            return self.parent.contains_shallow(group_names, classes)
        return False

    @property
    def is_child(self):
        """True if this entry nests under a class (is a method)."""
        return self.__method is not None

    def mark_as_child(self, method):
        """Marks this as a child so it won't be iterated as a top-level item.

        Needed for TestMethods. In Python we decorate functions, not methods,
        as the decorator doesn't know if a function is a method until later.
        So we end up storing entries in the Registry's list, but may only
        want to iterate through these from the parent onward. Finding each item
        in the list would be a waste of time, so instead we just mark them
        as such and ignore them during iteration.
        
        """
        self.__method = method
        self.homes = set([self.home, self.__method.im_class])

    def mark_as_used_by_factory(self):
        """If a Factory returns an instance of a class, the class will not
        also be run by Proboscis the usual way (only factory created instances
        will run).
        """
        self.__used_by_factory = True

    @property
    def method(self):
        """Returns the method represented by this test, if any.

        If this is not None, its im_func will be the same as 'home'.
        
        """
        return self.__method

    @property
    def used_by_factory(self):
        """True if instances of this are returned by a @factory."""
        return self.__used_by_factory

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
        super(TestMethodClassEntry, self).__init__(home, info)
        self.children = children
        for child in self.children:
            child.parent = self

    def contains(self, group_names, classes):
        """True if this belongs to any of the given groups or classes."""
        if contains_shallow(group_names, classes):
            return True
        for entry in self.children:
            if entry.contains(group_names, classes):
                return True
        return False

    def contains_shallow(self, group_names, classes):
        return super(TestMethodClassEntry, self).contains(group_names, classes)


from proboscis.case import TestPlan
from proboscis.case import test_runner_cls

class TestRegistry(object):
    """Stores test information."""
    def __init__(self):
        self.reset()

    def _change_function_to_method(self, method, cls_info):
        """Add an entry to a method by altering its function entry."""
        method_entry = method.im_func._proboscis_entry_
        method_entry.mark_as_child(method)
        new_groups = method_entry.info.inherit(cls_info)
        for group_name in new_groups:
            group = self.get_group(group_name)
            group.add_entry(method_entry)
        return method_entry

    def ensure_group_exists(self, group_name):
        """Adds the group if it does not exist."""
        if not group_name in self.groups:
            self.groups[group_name] = TestGroup(group_name)

    def get_group(self, group_name):
        """Finds a group by name."""
        self.ensure_group_exists(group_name)
        return self.groups[group_name]

    def get_test_plan(self):
        """Returns a sorted TestPlan that can be filtered."""
        return TestPlan(self.groups, self.tests, self.factories)

    @staticmethod
    def _mark_home_with_entry(entry):
        """Store the entry inside the function or class it represents.

        This way, non-unittest.TestCase classes can later find information on
        the methods they own, and so that info can be discovered for the
        instances returned by factories.

        """
        if entry.home is not None:
            if hasattr(entry.home, '_proboscis_entry_'):
                # subclasses will get this attribute from their parents.
                if entry.home._proboscis_entry_.home == entry.home:
                    raise RuntimeError("A test decorator or registration was "
                        "applied twice to the class or function %s." %
                        entry.home)
            # Assign reference so factories can discover it using an instance.
            entry.home._proboscis_entry_ = entry

    def register(self, test_home=None, **kwargs):
        """Registers a bit of code (or nothing) to be run / ordered as a test.

        Registering a test with nothing allows for the creation of groups of
        groups, which can be useful for organization.

        """
        info = TestEntryInfo(**kwargs)
        if test_home is None:
            return self._register_empty_test_case(info)
        elif isinstance(test_home, types.FunctionType):
            return self._register_func(test_home, info)
        elif issubclass(test_home, unittest.TestCase):
            return self._register_unittest_test_case(test_home, info)
        else:
            return self._register_test_class(test_home, info)

    def register_factory(self, func):
        """Turns a function into a Proboscis test instance factory.

        A factory returns a list of test class instances. Proboscis runs all
        factories at start up and sorts the instances like normal tests.
        
        """
        self.factories.append(func)

    def _register_empty_test_case(self, info):
        """Registers an 'empty' test."""
        self._register_simple_entry(None, info)
        return None

    def _register_unittest_test_case(self, test_cls, info):
        """Registers a unittest.TestCase."""
        entry = self._register_simple_entry(test_cls, info)
        return entry.home

    def _register_func(self, func, info):
        """Registers a function."""
        entry = self._register_simple_entry(func, info)
        return entry.home

    def _register_entry(self, entry):
        """Adds an entry to this Registry's list and may also create groups."""
        info = entry.info
        for group_name in info.groups:
            group = self.get_group(group_name)
            group.add_entry(entry)
        for group_name in info.depends_on_groups:
            self.ensure_group_exists(group_name)
        if entry.home:
            if not entry.home in self.classes:
                self.classes[entry.home] = []
            self.classes[entry.home].append(entry)
            self._mark_home_with_entry(entry)
        self.tests.append(entry)

    def _register_simple_entry(self, test_home, info):
        """Registers a unitttest style test entry."""
        entry = TestEntry(test_home, info)
        self._register_entry(entry)
        return entry

    def _register_test_class(self, cls, info):
        """Registers the methods within a class."""
        test_entries = []
        members = inspect.getmembers(cls, inspect.ismethod)
        before_class_methods = []
        after_class_methods = []
        for member in members:
            method = member[1]
            if hasattr(method, 'im_func'):
                func = method.im_func
                if hasattr(func, "_proboscis_entry_"):
                    entry = self._change_function_to_method(method, info)
                    test_entries.append(entry)
                    if entry.info.before_class:
                        before_class_methods.append(entry)
                    elif entry.info.after_class:
                        after_class_methods.append(entry)
        for before_entry in before_class_methods:
            for test_entry in test_entries:
                if not test_entry.info.before_class:
                    test_entry.info.depends_on.add(before_entry.home)
        for after_entry in after_class_methods:
            for test_entry in test_entries:
                if not test_entry.info.after_class:
                    after_entry.info.depends_on.add(test_entry.home)
        entry = TestMethodClassEntry(cls, info, test_entries)
        self._register_entry(entry)
        return entry.home

    def reset(self):
        """Wipes the registry."""
        self.tests = []
        self.groups = {}
        self.classes = {}
        self.factories = []


DEFAULT_REGISTRY = TestRegistry()


def register(**kwargs):
    """Registers a test in proboscis's default registry."""
    DEFAULT_REGISTRY.register(**kwargs)


def test(home=None, **kwargs):
    """Put this on a test class to cause Proboscis to run it. """
    if home:
        return DEFAULT_REGISTRY.register(home, **kwargs)
    else:
        def cb_method(home_2):
            return DEFAULT_REGISTRY.register(home_2, **kwargs)
        return cb_method


def before_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    kwargs.update({'run_before_class':True})
    return test(home=home, **kwargs)


def after_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    kwargs.update({'run_after_class':True})
    return test(home=home, **kwargs)


def factory(func=None, **kwargs):
    """A factory method returns new instances of Test classes."""
    if func:
        return DEFAULT_REGISTRY.register_factory(func)
    else:
        def cb_method(func_2):
            return DEFAULT_REGISTRY.register_factory(func_2, **kwargs)
        return cb_method



class TestProgram(dependencies.TestProgram):
    """The entry point of Proboscis.

    Creates the test suite and loaders before handing things off to Nose which
    runs as usual.

    """
    def __init__(self,
                 registry=DEFAULT_REGISTRY,
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
        argv = argv or sys.argv
        argv = self.extract_groups_from_argv(argv, groups)
        if "suite" in kwargs:
            raise ValueError("'suite' is not a valid argument, as Proboscis " \
                             "creates the suite.")

        self.__loader = testLoader or unittest.TestLoader()

        if OVERRIDE_DEFAULT_STREAM:
            stream = OVERRIDE_DEFAULT_STREAM

        if env is None:
            env = os.environ
        if dependencies.use_nose and config is None:
            config = self.makeConfig(env, plugins)
            if not stream:
                stream = config.stream

        stream = stream or sys.stdout
        
        if testRunner is None:
            runner_cls = test_runner_cls(dependencies.TextTestRunner,
                                         "ProboscisTestRunner")
            if dependencies.use_nose:
                testRunner = runner_cls(stream,
                                        verbosity=3,  # config.verbosity,
                                        config=config)
            else:
                testRunner = runner_cls(stream, verbosity=3)
                
        #registry.sort()
        self.plan = registry.get_test_plan()
        
        if len(groups) > 0:
            self.plan.filter(group_names=groups)
        self.cases = self.plan.tests
        if "--show-plan" in argv:
            self.__run = self.show_plan
        else:
            self.__suite = self.create_test_suite_from_entries(config,
                                                               self.cases)
            def run():
                if dependencies.use_nose:
                    dependencies.TestProgram.__init__(
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
                else:
                    dependencies.TestProgram.__init__(
                        self,
                        suite=self.__suite,
                        config=config,
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
        for case in self.cases:
            case.write_doc(sys.stdout)
    
    @property
    def test_suite(self):
        return self.__suite
