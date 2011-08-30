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


class TestEntryInfo:
    """Represents metadata attached to some kind of test code."""

    def __init__(self,
                 groups=None,
                 depends_on=None,
                 depends_on_classes=None,
                 depends_on_groups=None,
                 enabled=True,
                 always_run=False,
                 before_class=False,
                 after_class=False):
        groups = groups or []
        depends_on = set(depends_on or [])
        depends_on_classes = depends_on_classes or []
        for cls in depends_on_classes:
            depends_on.add(cls)
        depends_on_groups = depends_on_groups or []
        self.groups = groups
        self.depends_on = depends_on
        self.depends_on_groups = depends_on_groups
        self.enabled = enabled
        self.always_run = always_run
        self.inherit_groups=False
        self.before_class = before_class
        self.after_class = after_class
        if before_class and after_class:
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
        #TODO: Determine how this should work.
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

    def __init__(self, home_im_class, home, info):
        self.home_im_class = home_im_class
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
        return False

    @property
    def is_child(self):
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
        return self.__method

    def write_doc(self, file):
        file.write(str(self.home) + "\n")
        doc = pydoc.getdoc(self.home)
        if doc:
            file.write(doc + "\n")
        for field in str(self.info).split(', '):
            file.write("\t" + field + "\n")

    @property
    def used_by_factory(self):
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
        super(TestMethodClassEntry, self).__init__(None, home, info)
        self.children = children
        for child in self.children:
            child.parent = self

    def contains(self, group_names, classes):
        """True if this belongs to any of the given groups or classes."""
        if super(TestMethodClassEntry, self).contains(group_names, classes):
            return True
        for entry in children:
            if entry.contains(group_names, classes):
                return True
        return False

#
#def find_entry_for_instance(instance):
#    """Given an instance, return the attached TestEntry or raise."""
#    if isinstance(instance, types.MethodType):
#        raise RuntimeError("Method %s is not an instance.")
#        func = instance.im_func
#        try:
#            return func._proboscis_entry_
#        except AttributeError:
#            raise RuntimeError("Method %s is not decorated as a test." %
#                               instance)
#    if isinstance(instance, type):
#        raise RuntimeError("Factory %s returned type %s (rather than an "
#            "instance), which is not allowed." % (factory, instance))
#    if isinstance(instance, types.FunctionType):
#        home = instance
#    else:
#        home = type(instance)
#    if issubclass(home, unittest.TestCase):
#        raise RuntimeError("Factory %s returned a unittest.TestCase "
#            "instance %s, which is not legal.")
#    try:
#        entry = home._proboscis_entry_
#    except AttributeError:
#        raise RuntimeError("Factory method %s returned an instance %s "
#            "which was not tagged as a Proboscis TestEntry." %
#            (factory, instance))
#    # There is potentially an issue in that a different Registry might
#    # register an entry, and we could then read that in with a factory.
#    # Later the entry would not be found in the dictionary of entries.
#    state = TestMethodState(entry, instance)
#    return TestPlan._create_test_cases_for_entry(entry, state)


from proboscis.case import TestPlan
from proboscis.case import test_runner_cls

class TestRegistry(object):
    """Stores test information."""
    def __init__(self):
        self.reset()

    def _change_function_to_method(self, method, cls_info):
        """Add an entry to a method by altering its function entry."""
        cls = method.im_class
        #func = method.im_func
        method_entry = method.im_func._proboscis_entry_
        method_entry.mark_as_child(method)
        #method_entry.home = method
        new_groups = method_entry.info.inherit(cls_info)
        for group_name in new_groups:
            group = self.get_group(group_name)
            group.add_entry(method_entry)
        #entry = self._register_function_or_unittest_testcase(cls, method, method_info)
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

#    def _mark_function_with_metadata(self, function, info):
#        """Attaches info to a function for later reading.
#
#        Because the decorated method is not yet seen as connected to the class
#        all we can do is add the info to it and inspect it later.
#
#        """
#        function._proboscis_info_=info
#        return function

    def _mark_home_with_entry(self, entry):
        """Store the entry inside the function or class it represents.

        This way, non-unittest.TestCase classes can later find information on
        the methods they own, and so that info can be discovered for the
        instances returned by factories.

        """
        if entry.home is not None:
            if hasattr(entry.home, '_proboscis_entry_'):
                raise RuntimeError("A test decorator or registration was "
                    "applied twice to the class or function %s." % entry.home)
            # Assign reference so factories can discover it using an instance.
            entry.home._proboscis_entry_ = entry

    def register(self, test_home=None, **kwargs):
        info = TestEntryInfo(**kwargs)
        if test_home is None:
            return self.register_empty_test_case(info)
        elif isinstance(test_home, types.FunctionType):
            return self._register_func(test_home, info)
        elif issubclass(test_home, unittest.TestCase):
            return self.register_unittest_test_case(test_home, info)
        else:
            return self._register_test_class(test_home, info)

    def register_factory(self, func):
        self.factories.append(func)

    def register_empty_test_case(self, info):
        entry = self._register_function_or_unittest_testcase(None, None, info)
        return None

    def register_unittest_test_case(self, test_cls, info):
        entry = self._register_function_or_unittest_testcase(None, test_cls, info)
        return entry.home

    #deprecated
    def register_func(self, func, **kwargs):
        info = TestEntryInfo(**kwargs)
        if not isinstance(func, types.FunctionType):
            raise RuntimeError("Expected a function.")
        entry = self._register_function_or_unittest_testcase(None, func, info)
        #self._mark_home_with_entry(entry)
        #self.tests.append(entry)
        #self._register_entry(entry)
        return entry.home

    def _register_func(self, func, info):
        entry = self._register_function_or_unittest_testcase(None, func, info)
        #self._register_entry(entry)
#        self._mark_home_with_entry(entry)
#        self.tests.append(entry)
        return entry.home

    def _register_entry(self, entry):
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

    def _register_function_or_unittest_testcase(self, test_im_class, test_home, info):
        """Registers a unitttest style test entry."""
        entry = TestEntry(test_im_class, test_home, info)
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


#def test_func(home=None, **kwargs):
#    """Put this on a free-standing function to register it correctly."""
#    if home:
#        return default_registry.register_func(home)
#    else:
#        def cb_method(home_2):
#            return default_registry.register_func(home_2, **kwargs)
#        return cb_method

def before_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    if home:
        return default_registry.register(home, before_class=True)
    else:
        def cb_method(home_2):
            return default_registry.register(home_2, before_class=True,
                                             **kwargs)
        return cb_method


def after_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    if home:
        return default_registry.register(home, after_class=True)
    else:
        def cb_method(home_2):
            return default_registry.register(home_2, after_class=True,
                                             **kwargs)
        return cb_method


def factory(func=None, **kwargs):
    """A factory method returns new instances of Test classes."""
    if func:
        return default_registry.register_factory(func)
    else:
        def cb_method(func_2):
            return default_registry.register_factory(func_2, **kwargs)
        return cb_method


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
        self.cases = self.plan.tests
        if "--show-plan" in argv:
            self.__run = self.show_plan
        else:
            self.__suite = self.create_test_suite_from_entries(config,
                                                               self.cases)
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
        for case in self.cases:
            case.write_doc(sys.stdout)
    
    @property
    def test_suite(self):
        return self.__suite
