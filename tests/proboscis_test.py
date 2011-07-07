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

from proboscis.decorators import expect_exception
from proboscis.decorators import time_out
from proboscis.decorators import TimeoutError

# We can't import Proboscis classes here or Nose will try to run them as tests.

def assert_sort_order_is_correct(result):
    """Tests the result of a sort."""
    # TODO(tim.simpson): Clean this up, its kind of confusing.
    for i in range(len(result)):
        entry = result[i]
        for d in entry.info.depends_on_classes:
            for j in range(i, len(result)):
                if d is result[j].cls:
                    return "Invalid sort: " + str(entry) + " appears " + \
                           " before " + str(result[j]) + " but depends on it."
        for d in entry.info.depends_on_groups:
            for j in range(i, len(result)):
                for g in result[j].groups:
                    if d == g:
                        return "Invalid sort: " + str(entry) + \
                                  " depends on group " + d + ", but " \
                                  "appears before " + str(result[j]) + \
                                  " which is itself in group " + g + "."

# Fake classes we use as Nodes
class N2:
    pass
class N3:
    pass
def N5():
    pass
def N7():
    pass
class N8:
    pass
class N9:
    pass
def N10():
    pass
class N11:
    pass

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

    def test_simple_sort(self):
        from proboscis import TestGraph
        from proboscis import TestRegistry
        registry = TestRegistry()
        registry.register(N2, groups=["blah"], depends_on_classes=[N11])
        registry.register(N3, depends_on_classes=[N11, N2])
        registry.register(N7, depends_on_groups=["blah"])
        registry.register(N11)
        graph = TestGraph(registry)
        sorted_entries = graph.sort()
        result = list(entry.cls for entry in sorted_entries)
        expected = [N11, N2, N3, N7]
        self.assertEqual(4, len(result))
        self.assertEqual(N11, result[0])
        self.assertEqual(N2, result[1])
        self.assertTrue((result[2] == N3 and result[3] == N7) or \
                        (result[2] == N7 or result[3] == N2))

    def test_complex_sort(self):
        from proboscis import TestGraph
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
        graph = TestGraph(registry)  # sort the TestEntry instances
        result = graph.sort()
        self.assertEqual(8, len(result))
        msg = assert_sort_order_is_correct(result)
        self.assertEqual(None, msg)


    def test_do_not_allow_sneaky_cycle(self):
        from proboscis import TestGraph
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
        graph = TestGraph(registry)  # sort the TestEntry instances
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
        
        old_default_registry = proboscis.default_registry
        proboscis.default_registry = TestRegistry()
        reload(proboscis_example)
        self.registry = proboscis.default_registry
        proboscis.default_registry = old_default_registry
        self.registry.sort()

    def test_should_load_correct_number_of_tests(self):
        self.assertEqual(5, len(self.registry.get_sorted_tests()))

    def test_startup_must_be_first(self):
        from proboscis_example import StartUp
        self.assertEquals(StartUp, self.registry.get_sorted_tests()[0].cls)

    def test_filter_with_one(self):
        self.registry.filter_test_list(group_names=["init"])
        filtered = self.registry.get_sorted_tests()
        self.assertEqual(1, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].cls)

    def test_filter_should_keep_dependencies(self):
        self.registry.filter_test_list(group_names=["integration"])
        filtered = self.registry.get_sorted_tests()
        # Should include "integration" group and also "init" group since it
        # is a dependency.
        self.assertEqual(4, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].cls)
        # All the other ones must be in the integration group
        for i in range(1, 4):
            self.assertEqual("integration", filtered[i].info.groups[0])

    def test_filter_with_classes(self):
        from proboscis_example import RandomTestOne
        self.registry.filter_test_list(classes=[RandomTestOne])
        filtered = self.registry.get_sorted_tests()
        # Should include RandomTestOne, which depends on RandomTestZero,
        # which depends on init
        self.assertEquals(3, len(filtered))
        from proboscis_example import StartUp
        self.assertEqual(StartUp, filtered[0].cls)
        from proboscis_example import RandomTestZero
        self.assertEqual(RandomTestZero, filtered[1].cls)
        self.assertEqual(RandomTestOne, filtered[2].cls)


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

    def __init__(self):
        self.fail_was_called = False

    def fail(self, msg):
        self.fail_was_called = True

    @expect_exception(TimeoutError)
    def exceptional_function(self):
        raise TimeoutError()

    @expect_exception(TimeoutError)
    def unexceptional_function(self):
        pass


class TestExpectExceptionDecorator(unittest.TestCase):

    def test_should_fail_if_no_exception_occurs(self):
        case = MockCase()
        case.unexceptional_function()
        self.assertTrue(case.fail_was_called)

    def test_should_not_fail_if_exception_occurs(self):
        case = MockCase()
        case.exceptional_function()
        self.assertFalse(case.fail_was_called)


