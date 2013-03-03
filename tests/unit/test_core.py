import imp
import sys
import time
import unittest


from proboscis.asserts import assert_equal
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis.asserts import assert_false
from proboscis.asserts import fail
from proboscis import compatability
from proboscis.compatability import get_method_function
from proboscis import decorators
from proboscis.decorators import expect_exception
from proboscis.decorators import time_out
from proboscis.decorators import TimeoutError
from proboscis import ProboscisTestMethodClassNotDecorated


class ProboscisRegistryTest(unittest.TestCase):

    def setUp(self):
        import proboscis
        from proboscis import TestRegistry
        self.old_default_registry = proboscis.decorators.DEFAULT_REGISTRY
        self.registry = TestRegistry()
        proboscis.decorators.DEFAULT_REGISTRY = self.registry

    def tearDown(self):
        import proboscis
        proboscis.decorators.DEFAULT_REGISTRY = self.old_default_registry


class ExampleTest(object):
    def test_1(self):
        pass


class TestClassDecoratorInheritanceForEnabled(ProboscisRegistryTest):

    def test_if_unset_then_func_should_inherit_enabled_false(self):
        from proboscis import test

        @test(enabled=False)
        class ExampleTest(object):
            @test
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home == ExampleTest:
                assert_false(t.info.enabled)
            if t.home == ExampleTest.test_1:
                assert_false(t.info.enabled)

    def test_if_set_then_func_should_not_inherit(self):
        from proboscis import test

        @test(enabled=False)
        class ExampleTest(object):
            @test(enabled=True)
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home == ExampleTest:
                assert_false(t.info.enabled)
            if t.home == ExampleTest.test_1:
                assert_true(t.info.enabled)

    def test_if_set_then_func_should_not_inherit(self):
        from proboscis import test

        @test(enabled=False)
        class ExampleTest(object):
            @test(enabled=False)
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home is ExampleTest:
                assert_false(t.info.enabled)
            elif t.home is get_method_function(ExampleTest.test_1):
                assert_false(t.info.enabled)
            else:
                fail("Unexpected test seen in iteration: %s" % t)


class TestClassDecoratorInheritanceForRunsAfter(ProboscisRegistryTest):

    def test_if_not_set_on_parent_func_is_unaffected(self):
        from proboscis import test

        @test
        def other_test():
            pass

        @test
        class ExampleTest(object):
            @test(runs_after=[other_test])
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home is ExampleTest:
                assert_equal(0, len(t.info.runs_after))
            elif t.home is get_method_function(ExampleTest.test_1):
                assert_equal(1, len(t.info.runs_after))
                assert_true(other_test in t.info.runs_after)
            elif t.home is not other_test:
                fail("Unexpected test seen in iteration: %s" % t)

    def test_if_set_on_parent_func_adds_parent_items_to_list(self):
        from proboscis import test

        @test
        def other_test():
            pass

        @test
        def yet_another_test():
            pass

        @test(runs_after=[yet_another_test])
        class ExampleTest(object):
            @test(runs_after=[other_test])
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home is ExampleTest:
                assert_equal(1, len(t.info.runs_after))
                assert_true(yet_another_test in t.info.runs_after)
            elif t.home is get_method_function(ExampleTest.test_1):
                assert_equal(2, len(t.info.runs_after))
                expected_homes = {other_test:False, yet_another_test:False}
                for home in t.info.runs_after:
                    if home not in expected_homes.keys():
                        fail("%s should not be in runs_after" % home)
                    expected_homes[home] = True
                for expected_home, found in expected_homes.items():
                    if not found:
                        fail("%s was not found in runs_after" % expected_home)
            elif t.home not in (other_test, yet_another_test):
                fail("Unexpected test seen in iteration: %s" % t)


class TestClassDecoratorInheritanceForRunsAfterGroups(ProboscisRegistryTest):

    def test_if_not_set_on_parent_func_is_unaffected(self):
        from proboscis import test

        @test
        class ExampleTest(object):
            @test(runs_after_groups=["other_test"])
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home == ExampleTest:
                assert_equal(0, len(t.info.runs_after_groups))
            elif t.home == get_method_function(ExampleTest.test_1):
                assert_equal(1, len(t.info.runs_after_groups))
                assert_true("other_test" in t.info.runs_after_groups)
            else:
                fail("Unexpected test seen in iteration: %s" % t)

    def test_if_set_on_parent_func_adds_parent_items_to_list(self):
        from proboscis import test

        @test(runs_after_groups=["yet_another_test"])
        class ExampleTest(object):
            @test(runs_after_groups=["other_test"])
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home == ExampleTest:
                assert_equal(1, len(t.info.runs_after_groups))
                assert_true("yet_another_test" in t.info.runs_after_groups)
            elif t.home == get_method_function(ExampleTest.test_1):
                assert_equal(2, len(t.info.runs_after_groups))
                expected_homes = {"other_test":False, "yet_another_test":False}
                for home in t.info.runs_after_groups:
                    if home not in expected_homes.keys():
                        fail("%s should not be in runs_after_groups" % home)
                    expected_homes[home] = True
                for expected_home, found in expected_homes.items():
                    if not found:
                        fail("%s was not found in runs_after_groups"
                             % expected_home)
            else:
                fail("Unexpected test seen in iteration: %s" % t)


class TestClassDecoratorInheritanceForAlwaysRun(ProboscisRegistryTest):

     def test_class_if_true_forces_child_to_true(self):
        from proboscis import test

        @test(always_run=True)
        class ExampleTest(object):
            @test(always_run=False)
            def test_1(self):
                pass

        for t in self.registry.tests:
            if t.home == ExampleTest:
                assert_true(t.info.enabled)
            if t.home == ExampleTest.test_1:
                assert_true(t.info.enabled)


class TestClassDecoratorInheritanceForDependsOn(ProboscisRegistryTest):

     def test_class_if_true_forces_child_to_true(self):
        from proboscis import test

        @test
        def dependency():
            pass

        @test(depends_on=[dependency])
        class ExampleTest(object):
            @test
            def test_1(self):
                pass
            @test(depends_on=[dependency])
            def test_2(self):
                pass

        for t in self.registry.tests:
            if t.home in (ExampleTest, ExampleTest.test_1, ExampleTest.test_2):
                assert_true(dependency in t.info.depends_on)

class TestClassDecoratorInheritanceForDependsOnGroups(ProboscisRegistryTest):

     def test_class_if_true_forces_child_to_true(self):
        from proboscis import test

        @test(depends_on_groups=["blah"])
        class ExampleTest(object):
            @test
            def test_1(self):
                pass
            @test(depends_on_groups=["blah"])
            def test_2(self):
                pass

        for t in self.registry.tests:
            if t.home in (ExampleTest, ExampleTest.test_1, ExampleTest.test_2):
                assert_true("blah" in t.info.depends_on_groups)


class TestCannotUseBothBeforeClassAndAfterClass(ProboscisRegistryTest):

     def test_wont_work(self):
        from proboscis.core import TestEntryInfo
        assert_raises(RuntimeError, TestEntryInfo, run_before_class=5,
                      run_after_class=6)


class TestEntryInfoRepr(unittest.TestCase):

    def test_it_doesnt_blow_up(self):
        from proboscis.core import TestEntryInfo
        repr(TestEntryInfo())


class TestCannotApplyDecoratorTwice(ProboscisRegistryTest):

    def test_cant_do_that(self):
        from proboscis import test
        def reg():
            @test
            @test
            def hi():
                pass
        assert_raises(RuntimeError, reg)
