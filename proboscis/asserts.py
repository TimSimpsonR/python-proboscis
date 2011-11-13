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

"""Assert functions with a parameter order of actual_value, expected_value.

This module is a clone of TestNG's Assert class with the static methods changed
to functions, and the term "equals" changed to simply "equal" as this seems
more Pythonic.

"""


import sys
import traceback

from proboscis import compatability

ASSERTION_ERROR=AssertionError

#TODO:
#def assert_equal with delta(actual, expected, delta):
#    """Asserts two numbers differ only by delta."""
#
#def assert_equal_no_order(actual, expected, message=None):
#    """Asserts that two iterables contain the same elements in any order."""

def assert_equal(actual, expected, message=None):
    """Asserts that the two values are equal."""
    #TODO: assert equal with dictionaries, arrays, etc
    if actual == expected:
        return
    if not message:
        try:
            message = "%s != %s" % (actual, expected)
        except Exception:
            message = "The actual value did not equal the expected one."
    raise ASSERTION_ERROR(message)


def assert_false(condition, message=None):
    if condition:
        if not message:
            message = "Condition was True."
        raise ASSERTION_ERROR(message)


def assert_is(actual, expected, message=None):
    """Asserts that the two values are equal."""
    #TODO: assert equal with dictionaries, arrays, etc
    if actual is expected:
        return
    if not message:
        try:
            message = "%s is not %s" % (actual, expected)
        except Exception:
            message = "The actual value is not the expected one."
    raise ASSERTION_ERROR(message)


def assert_is_none(value, message=None):
    """Asserts that the two values are equal."""
    #TODO: assert equal with dictionaries, arrays, etc
    if value is None:
        return
    if not message:
        try:
            message = "%s is not None" % value
        except Exception:
            message = "The value is not None."
    raise ASSERTION_ERROR(message)


def assert_is_not(actual, expected, message=None):
    """Asserts that the two values are equal."""
    #TODO: assert equal with dictionaries, arrays, etc
    if actual is not expected:
        return
    if not message:
        try:
            message = "%s is %s" % (actual, expected)
        except Exception:
            message = "The actual value is the expected one."
    raise ASSERTION_ERROR(message)


def assert_is_not_none(value, message=None):
    """Asserts that the two values are equal."""
    #TODO: assert equal with dictionaries, arrays, etc
    if value is not None:
        return
    if not message:
        try:
            message = "%s is None" % value
        except Exception:
            message = "The value is None."
    raise ASSERTION_ERROR(message)

def assert_not_equal(actual, expected, message=None):
    if actual != expected:
        return
    if not message:
        try:
            message = "%s == %s" % (actual, expected)
        except Exception:
            message = "The actual value equalled the expected one."
    raise ASSERTION_ERROR(message)


def assert_true(condition, message=None):
    if not condition:
        if not message:
            message = "Condition was False."
        raise ASSERTION_ERROR(message)


def assert_raises(exception_type, function, *args, **kwargs):
    """Calls function and fails the test if an exception is not raised.

    The exact type of exception must be thrown.

    """
    actual_exception = compatability.capture_exception(
        lambda : function(*args, **kwargs),
        exception_type)
    if actual_exception is None:
        fail("Expected an exception of type %s to be raised." % exception_type)
    elif type(actual_exception) != exception_type:
        _a, _b, tb = sys.exc_info()
        info = traceback.format_list(traceback.extract_tb(tb))
        fail("Expected a raised exception of type %s, but found type %s. "
            "%s" % (exception_type, type(actual_exception), info))


def assert_raises_instance(exception_type, function, *args, **kwargs):
    """Calls function and fails the test if an exception is not raised.

    The exception thrown must only be an instance of the given type.

    """
    actual_exception = compatability.capture_exception(
        lambda : function(*args, **kwargs),
        exception_type)
    if actual_exception is None:
        fail("Expected an exception of type %s to be raised.")


def fail(message=None):
    if not message:
        message = "Test failure."
    raise ASSERTION_ERROR(message)
