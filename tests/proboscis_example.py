# Copyright (c) 2011 OpenStack, LLC.
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

"""Example module loaded by proboscis_test."""

import unittest
from proboscis import test

_data_exists = False
_tests_run = [ False, False, False ]


@test(groups=["integration"], depends_on_groups=["init"])
class RandomTestZero(unittest.TestCase):

    def test_something(self):
        self.assertEquals(_data_exists)
        _tests_run[0] = True


@test(depends_on_groups=["integration"])
class Destroy(object):

    def test_destroy(self):
        assert _data_exists

@test(groups=["integration"], depends_on_groups=["init"],
      depends_on_classes=[RandomTestZero])
class RandomTestOne(object):

    def test_something(self):
        assert _data_exists
        _tests_run[1] = True

@test(groups=["integration"], depends_on_groups=["init"])
class RandomTestTwo(unittest.TestCase):

    def test_something(self):
        self.assertEquals(_data_exists)
        _tests_run[2] = True

@test(groups=["init"])
class StartUp(object):

    def test_connect_to_db(self):
        self.assertEquals(10, 10)
        global _data_exists
        _data_exists = True
