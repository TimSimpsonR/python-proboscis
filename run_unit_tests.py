import unittest
import sys
from tests.unit.test_asserts import *
if sys.version >= "2.6":  # These tests use "with".
    from tests.unit.test_check import *
from tests.unit.test_core import *
if sys.version >= "2.6":  # These tests use "with".
    from tests.unit.test_check import *
    from tests.unit.test_core_with import *
from tests.unit.test_sorting import *


if __name__ == '__main__':
    unittest.main()
