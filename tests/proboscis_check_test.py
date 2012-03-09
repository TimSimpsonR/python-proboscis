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


import unittest


from proboscis.check import Checker
from proboscis.asserts import ASSERTION_ERROR
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis.asserts import assert_false
from proboscis.asserts import fail


class TestChecker(unittest.TestCase):

    def test_when_no_failures_occur_nothing_happens(self):
        with Checker() as check:
            print("CEHCK:%s" % check)
            check.equal("HI", "HI")

    def test_single_failure_is_presented(self):
        try:
            with Checker() as check:
                check.equal(4, 6)
            fail("Expected an assertion!")
        except ASSERTION_ERROR as ae:
            assert_true("4 != 6" in str(ae), str(ae))

    def test_multiple_failures_are_presented(self):
        try:
            with Checker() as c:
                c.equal(2,27)
                c.equal("BEE", "BEE")
                c.equal(39, 37)
                c.equal("CAT", "RAT")
            fail("Expected an assertion!")
        except ASSERTION_ERROR as ae:
            msg = str(ae)
            assert_true("2 != 27" in msg, msg)
            assert_true("39 != 37" in msg, msg)
            assert_true("CAT != RAT" in msg, msg)

    def test_when_no_failures_happen_but_an_error_occurs(self):
        # The exception is *not* wrapped as ASSERTION_ERROR because no failures
        # occur.
        def check_func():
            with Checker() as c:
                c.equal(2,2)
                c.equal("BEE", "BEE")
                c.equal(37, 37)
                raise RuntimeError("Unexplained error!")
                c.equal("CAT", "RAT")
        assert_raises(RuntimeError, check_func)

    def test_when_failures_and_an_error_occurs(self):
        try:
            with Checker() as c:
                c.equal(2,27)
                c.equal("BEE", "BEE")
                c.equal(39, 37)
                raise RuntimeError("Unexplained error!")
                c.equal("CAT", "RAT")  # This is never reached.
        except ASSERTION_ERROR as ae:
            msg = str(ae)
            assert_true("2 != 27" in msg, msg)
            assert_true("39 != 37" in msg, msg)
            assert_false("CAT != RAT" in msg, msg)
            assert_true("RuntimeError: Unexplained error!" in msg, msg)




if __name__ == "__main__":
    unittest.TestProgram()
