import unittest
from proboscis import test


import utils


@test(groups=["unit"])
class TestReverseString(unittest.TestCase):

    def test_reversal(self):
        original = "hello"
        expected = "olleh"
        actual = utils.reverse(original)
        self.assertEqual(expected, actual)
