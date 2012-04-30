import unittest

from proboscis.asserts import ASSERTION_ERROR
from proboscis.asserts import assert_false
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_not_equal
from proboscis.asserts import assert_is
from proboscis.asserts import assert_is_none
from proboscis.asserts import assert_is_not
from proboscis.asserts import assert_is_not_none
from proboscis.asserts import assert_true
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_raises_instance
from proboscis.asserts import fail


class BadClass(object):

    def __str__(self):
        raise RuntimeError()


class MyException(RuntimeError):
    pass


class TestAsserts(unittest.TestCase):

    def fails(self, func, *args, **kwargs):
        self.assertRaises(ASSERTION_ERROR, func, *args, **kwargs)

    def fails_m(self, message, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except ASSERTION_ERROR as ae:
            self.assertEqual(message, str(ae))

    def test_equal1(self):
        assert_equal(2,2)

    def test_equal2(self):
        self.fails(assert_equal, 2, 4)

    def test_equal3(self):
        self.fails_m("Blah!", assert_equal, 2, 4, "Blah!")

    def test_equal4(self):
        self.fails_m("The actual value did not equal the expected one.",
                     assert_equal, BadClass(), BadClass())

    def test_false1(self):
        assert_false(False)

    def test_false2(self):
        self.fails(assert_false, True)

    def test_false3(self):
        self.fails_m("Blah!", assert_false, True, "Blah!")

    def test_is1(self):
        assert_is(2, 2)

    def test_is2(self):
        self.fails(assert_is, 2, 4)

    def test_is3(self):
        self.fails_m("Blah!", assert_is, 2, 4, "Blah!")

    def test_is4(self):
        self.fails_m("The actual value is not the expected one.",
                     assert_is, BadClass(), BadClass())

    def test_is_none1(self):
        assert_is_none(None)

    def test_is_none2(self):
        self.fails(assert_is_none, 2)

    def test_is_none3(self):
        self.fails_m("Blah!", assert_is_none, 2, "Blah!")

    def test_is_none4(self):
        self.fails_m("The value is not None.",
                     assert_is_none, BadClass())

    def test_is_not1(self):
        assert_is_not(None, 3)

    def test_is_not2(self):
        self.fails(assert_is_not, 2, 2)

    def test_is_not(self):
        self.fails_m("Blah!", assert_is_not, 2, 2, "Blah!")

    def test_is_not4(self):
        b = BadClass()
        self.fails_m("The actual value is the expected one.",
                     assert_is_not, b, b)

    def test_is_not_none1(self):
        assert_is_not_none(True)

    def test_is_not_none2(self):
        self.fails(assert_is_not_none, None)

    def test_is_not_none3(self):
        self.fails_m("Blah!", assert_is_none, None, "Blah!")

    def test_is_not_none4(self):
        self.fails_m("The value is not None.",
                     assert_is_not_none, BadClass())

    def test_not_equal1(self):
        assert_not_equal(2,4)

    def test_not_equal2(self):
        self.fails(assert_not_equal, 2, 2)

    def test_not_equal3(self):
        self.fails_m("Blah!", assert_not_equal, 2, 2, "Blah!")

    def test_not_equal4(self):
        self.fails_m("The actual value equalled the expected one.",
                     assert_not_equal, BadClass(), BadClass())

    def test_true1(self):
        assert_true(True)

    def test_true2(self):
        self.fails(assert_true, False)

    def test_true3(self):
        self.fails_m("Blah!", assert_true, False, "Blah!")

    def test_fail(self):
        self.fails_m("Blah!", fail, "Blah!")

    def test_assert_raises1(self):
        def correct():
            raise RuntimeError()
        assert_raises(RuntimeError, correct)

    def test_assert_raises2(self):
        def not_correct():
            pass
        self.fails(assert_raises, RuntimeError, not_correct)

    def test_assert_raises3(self):
        def not_precise():
            raise MyException()  # Even a derived class won't work.
        self.fails(assert_raises, RuntimeError, not_precise)

    def test_assert_raises4(self):
        def not_precise():
            raise Exception("HELLO!!")
        try:
            assert_raises(RuntimeError, not_precise)
        except Exception as ex:
            # Make sure we're getting the original.
            self.assertEquals("HELLO!!", str(ex))
