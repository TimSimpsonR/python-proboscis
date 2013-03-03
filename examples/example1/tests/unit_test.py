import unittest
import mymodule
from proboscis import test

@test(groups=["unit"])
class TestReverseString(unittest.TestCase):

    def test_reversal(self):
        original = "hello"
        expected = "olleh"
        actual = mymodule.reverse(original)
        self.assertEqual(expected, actual)