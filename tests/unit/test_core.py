import imp
import sys
import time
import unittest


from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis.asserts import assert_false
from proboscis import compatability
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
            if t.home == ExampleTest:
                assert_false(t.info.enabled)
            if t.home == ExampleTest.test_1:
                assert_false(t.info.enabled)


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
