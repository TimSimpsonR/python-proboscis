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

"""Tests the internal logic of the proboscis module."""

import time
import unittest

from nose import core
from proboscis.asserts import assert_raises

from proboscis.decorators import expect_exception
from proboscis.decorators import time_out
from proboscis.decorators import TimeoutError

# We can't import Proboscis classes here or Nose will try to run them as tests.

def assert_sort_order_is_correct(result):
    """Tests the result of a sort."""
    # TODO(tim.simpson): Clean this up, its kind of confusing.
    for i in range(len(result)):
        case = result[i]
        for d in case.entry.info.depends_on:
            for j in range(i, len(result)):
                if d is result[j].entry.home:
                    return "Invalid sort: " + str(case) + " appears " + \
                           " before " + str(result[j]) + " but depends on it."
        for d in case.entry.info.depends_on_groups:
            for j in range(i, len(result)):
                for g in result[j].groups:
                    if d == g:
                        return "Invalid sort: " + str(case) + \
                                  " depends on group " + d + ", but " \
                                  "appears before " + str(result[j]) + \
                                  " which is itself in group " + g + "."


# Fake classes we use as Nodes
class N2(unittest.TestCase):
    pass
class N3(unittest.TestCase):
    pass
def N5():
    pass
def N7():
    pass
class N8(unittest.TestCase):
    pass
class N9(unittest.TestCase):
    pass
def N10():
    pass
class N11(unittest.TestCase):
    pass


def remove_entry(home):
    """Proboscis fails if a class or function is registry twice.
    This prevents that."""
    if hasattr(home, '_proboscis_entry_'):
        delattr(home, '_proboscis_entry_')

def remove_entries():
    for item in [N2, N3, N5, N7, N8, N9, N10, N11]:
        remove_entry(item)

class TestValidation(unittest.TestCase):

    def test_should_not_allow_group_to_depend_on_self(self):
        from proboscis import TestRegistry
        registry = TestRegistry()
        try:
            registry.register(N2, groups=["tests"],
                              depends_on_groups=["tests"])
            self.fail("Expected runtime error.")
        except RuntimeError:
            pass

    def test_should_not_allow_classes_to_depend_on_self(self):
        from proboscis import TestRegistry
        registry = TestRegistry()
        try:
            registry.register(N2, depends_on_classes=[N2])
            self.fail("Expected runtime error.")
        except RuntimeError:
            pass


class TestTopologicalSort(unittest.TestCase):

    def setUp(self):
       remove_entries()

    def test_simple_sort(self):
        from proboscis.case import TestPlan
        from proboscis.sorting import TestGraph
        from proboscis import TestRegistry
        registry = TestRegistry()
        registry.register(N2, groups=["blah"], depends_on_classes=[N11])
        registry.register(N3, depends_on_classes=[N11, N2])
        registry.register(N7, depends_on_groups=["blah"])
        registry.register(N11)
        cases = TestPlan.create_cases(registry.tests, [])
        graph = TestGraph(registry.groups, registry.tests, cases)
        sorted_entries = graph.sort()
        result = list(case.entry.home for case in sorted_entries)
        expected = [N11, N2, N3, N7]
        self.assertEqual(4, len(result))
        self.assertEqual(N11, result[0])
        self.assertEqual(N2, result[1])
        self.assertTrue((result[2] == N3 and result[3] == N7) or \
                        (result[2] == N7 or result[3] == N2))

    def test_complex_sort(self):
        from proboscis.case import TestPlan
        from proboscis.sorting import TestGraph
        from proboscis import TestRegistry

        registry = TestRegistry()
        registry.register(N2, depends_on_classes=[N11])
        registry.register(N3)
        registry.register(N5)
        registry.register(N7)
        registry.register(N8, depends_on_classes=[N3])
        registry.register(N9, depends_on_classes=[N8, N11])
        registry.register(N10, depends_on_classes=[N3, N11])
        registry.register(N11, depends_on_classes=[N5, N7])
        cases = TestPlan.create_cases(registry.tests, [])
        graph = TestGraph(registry.groups, registry.tests, cases)
        result = graph.sort()
        self.assertEqual(8, len(result))
        msg = assert_sort_order_is_correct(result)
        self.assertEqual(None, msg)


    def test_do_not_allow_sneaky_cycle(self):
        from proboscis.case import TestPlan
        from proboscis.sorting import TestGraph
        from proboscis import TestRegistry

        registry = TestRegistry()
        registry.register(N2, depends_on_classes=[N11])
        registry.register(N3)
        registry.register(N5, depends_on_groups=["something"])
        registry.register(N7)
        registry.register(N8, depends_on_classes=[N3])
        registry.register(N9, depends_on_classes=[N8, N11])
        registry.register(N10, depends_on_classes=[N3, N11])
        registry.register(N11, groups=["something"],
                          depends_on_classes=[N5, N7])
        cases = TestPlan.create_cases(registry.tests, [])
        graph = TestGraph(registry.groups, registry.tests, cases)
        try:
            result = graph.sort()
            self.fail("A cycle has escaped us.")
        except RuntimeError as re:
            self.assertTrue(str(re).find("Cycle found") >= 0)

class TestModuleConversionToNodes(unittest.TestCase):

    def setUp(self):
        import proboscis
        import proboscis_example
        from proboscis import TestRegistry
        
        old_default_registry = proboscis.DEFAULT_REGISTRY
        proboscis.DEFAULT_REGISTRY = TestRegistry()
        reload(proboscis_example)
        self.registry = proboscis.DEFAULT_REGISTRY
        proboscis.default_registry = old_default_registry
        self.plan = self.registry.get_test_plan()

    def test_should_load_correct_number_of_tests(self):
        self.assertEqual(5, len(self.plan.tests))

    def test_startup_must_be_first(self):
        from proboscis_example import StartUp
        self.assertEquals(StartUp, self.plan.tests[0].entry.home)

    def test_filter_with_one(self):
        self.plan.filter(group_names=["init"])
        filtered = self.plan.tests
        self.assertEqual(1, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].entry.home)

    def test_filter_should_keep_dependencies(self):
        self.plan.filter(group_names=["integration"])
        filtered = self.plan.tests
        # Should include "integration" group and also "init" group since it
        # is a dependency.
        self.assertEqual(4, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].entry.home)
        # All the other ones must be in the integration group
        for i in range(1, 4):
            self.assertEqual("integration", filtered[i].entry.info.groups[0])

    def test_filter_with_classes(self):
        from proboscis_example import RandomTestOne
        self.plan.filter(classes=[RandomTestOne])
        filtered = self.plan.tests
        # Should include RandomTestOne, which depends on RandomTestZero,
        # which depends on init
        self.assertEquals(3, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].entry.home)
        from proboscis_example import RandomTestZero
        self.assertEqual(RandomTestZero, filtered[1].entry.home)
        self.assertEqual(RandomTestOne, filtered[2].entry.home)


@time_out(2)
def lackadaisical_multiply(a, b):
    sum = 0
    for i in range(0, b):
        time.sleep(1)
        sum = sum + a
    return sum


class TestTimeoutDecorator(unittest.TestCase):

    def test_should_not_time_out_before_time_exceeded(self):
        self.assertEqual(0, lackadaisical_multiply(4, 0))
        self.assertEqual(8, lackadaisical_multiply(8, 1))

    def test_should_timeout_if_time_exceeded(self):
        try:
            self.assertEqual(8 * 8, lackadaisical_multiply(8, 8))
            self.fail("time_out decorator did not work.")
        except TimeoutError:
            pass

class MockCase(object):

    @expect_exception(TimeoutError)
    def broadly_exceptional_function(self):
        raise Exception()

    @expect_exception(TimeoutError)
    def exceptional_function(self):
        raise TimeoutError()

    @expect_exception(TimeoutError)
    def unexceptional_function(self):
        pass

    @expect_exception(Exception)
    def broadly_decorated_function(self):
        raise TimeoutError()


class TestExpectExceptionDecorator(unittest.TestCase):

    def test_should_fail_if_no_exception_occurs(self):
        case = MockCase()
        self.assertRaises(AssertionError, case.unexceptional_function)

    def test_should_fail_if_incorrect_exception_occurs(self):
        case = MockCase()
        # The original exception is raised unfiltered
        self.assertRaises(Exception, case.broadly_exceptional_function)

    def test_should_not_fail_if_exception_occurs(self):
        case = MockCase()
        case.exceptional_function()

    def test_should_fail_if_incorrect_exception_occurs(self):
        case = MockCase()
        case.broadly_decorated_function()


class TestAssertRaises(unittest.TestCase):

    def test_should_fail_if_no_exception_occurs(self):
        def throw_time_out():
            pass
        self.assertRaises(AssertionError, assert_raises, TimeoutError,
                          throw_time_out)

    def test_should_fail_if_incorrect_exception_occurs(self):
        def throw_time_out():
            raise Exception()
        self.assertRaises(AssertionError, assert_raises, TimeoutError,
                          throw_time_out)

    def test_should_not_fail_if_exception_occurs(self):
        def throw_time_out():
            raise TimeoutError()
        assert_raises(TimeoutError, throw_time_out)

    def test_should_fail_if_incorrect_exception_occurs(self):
        """The subclass is not good enough for assert_raises."""
        def throw_time_out():
            raise TimeoutError()
        self.assertRaises(AssertionError, assert_raises, Exception,
                          throw_time_out)



class TestMethodMarker(unittest.TestCase):

    def setUp(self):
        import proboscis
        from proboscis import TestRegistry
        self.old_default_registry = proboscis.DEFAULT_REGISTRY
        proboscis.DEFAULT_REGISTRY = TestRegistry()

    def tearDown(self):
        import proboscis
        proboscis.DEFAULT_REGISTRY = self.old_default_registry

    def test_should_mark_methods(self):
        import proboscis
        from proboscis import test

        class Example(object):

            def __init__(self):
                self.a = 5

            @test
            def something(self):
                """This tests something."""
                self.a = 55

        self.assertTrue(hasattr(Example.something, '_proboscis_entry_'))
        self.assertTrue(hasattr(Example.something.im_func, '_proboscis_entry_'))
