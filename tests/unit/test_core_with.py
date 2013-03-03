import unittest
from tests.unit.test_core import ProboscisRegistryTest


class TestClassMethodEntry(ProboscisRegistryTest):

     def test_method_im_class_points_to_class(self):
        from proboscis import test
        from proboscis.asserts import Check

        @test
        def func1():
            pass

        @test(groups=["top_level_class_group"])
        class ExampleTest(object):
            @test
            def test_1(self):
                pass

        with Check() as check:
            for t in self.registry.tests:
                if t.home == ExampleTest:
                    pass
                elif t.home == ExampleTest.test_1:
                    if not t.is_child:
                        check.fail("Test Entry did not mark method as such!")
                    else:
                        check.true(ExampleTest in t.homes,
                                   "Class was not stored in 'homes' property.")
                        check.true(ExampleTest.test_1 in t.homes,
                                   "Method was not stored in 'homes' property.")
                        check.equal(t.method, ExampleTest.test_1)
                    # Just make sure this doesn't blow up...
                    repr(t)
                elif t.home == func1:
                    check.is_none(t.method)


class TestClassContainsAndMethodProp(ProboscisRegistryTest):

     def test_contains_searches_methods(self):
        from proboscis import test
        from proboscis.asserts import Check

        class Unrelated(object):
            def func1(self):
                pass

        @test(groups=["top_level_class_group"])
        class ExampleTest(object):
            @test
            def test_1(self):
                pass
            @test(groups=["test_2_group"])
            def test_2(self):
                pass

        with Check() as check:
            for t in self.registry.tests:
                if t.home == ExampleTest:
                    check.false(t.contains(["bjkjd"], []))
                    check.true(t.contains(["top_level_class_group"], []))
                    check.false(t.contains([], [Unrelated]))
                    check.true(t.contains(["test_2_group"], []))
                    check.true(t.contains([], [ExampleTest]))
                elif t.home == ExampleTest.test_1:
                    check.false(t.contains(["bjkjd"], []))
                    check.true(t.contains(["top_level_class_group"], []))
                    check.false(t.contains([], [Unrelated]))
                    check.false(t.contains(["test_2_group"], []))
                    check.true(t.contains([], [ExampleTest]))
                elif t.home == ExampleTest.test_2:
                    check.false(t.contains(["bjkjd"], []))
                    check.true(t.contains(["top_level_class_group"], []))
                    check.false(t.contains([], [Unrelated]))
                    check.true(t.contains(["test_2_group"], []))
                    check.true(t.contains([], [ExampleTest]))
