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

"""Decorators useful to the tests."""

import signal

from functools import wraps

from proboscis.asserts import assert_raises_instance
from proboscis import compatability
from proboscis.core import TestRegistry


DEFAULT_REGISTRY = TestRegistry()


def expect_exception(exception_type):
    """Decorates a test method to show it expects an exception to be raised."""
    def return_method(method):
        @wraps(method)
        def new_method(*args, **kwargs):
            assert_raises_instance(exception_type, method, *args, **kwargs)
        return new_method
    return return_method


class TimeoutError(RuntimeError):
    """Thrown when a method has exceeded the time allowed."""
    pass


def time_out(time):
    """Raises TimeoutError if the decorated method does not finish in time."""
    if compatability.is_jython():
        raise ImportError("Not supported.")

    def cb_timeout(signum, frame):
        raise TimeoutError("Time out after waiting " + str(time) + " seconds.")

    def return_method(func):
        """Turns function into decorated function."""
        @wraps(func)
        def new_method(*kargs, **kwargs):
            previous_handler = signal.signal(signal.SIGALRM, cb_timeout)
            try:
                signal.alarm(time)
                return func(*kargs, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, previous_handler)
        return new_method
    return return_method


def register(**kwargs):
    """Registers a test in proboscis's default registry."""
    DEFAULT_REGISTRY.register(**kwargs)


def test(home=None, **kwargs):
    """Put this on a test class to cause Proboscis to run it. """
    if home:
        return DEFAULT_REGISTRY.register(home, **kwargs)
    else:
        def cb_method(home_2):
            return DEFAULT_REGISTRY.register(home_2, **kwargs)
        return cb_method


def before_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    kwargs.update({'run_before_class':True})
    return test(home=home, **kwargs)


def after_class(home=None, **kwargs):
    """Like @test but indicates this should run before other class methods."""
    kwargs.update({'run_after_class':True})
    return test(home=home, **kwargs)


def factory(func=None, **kwargs):
    """A factory method returns new instances of Test classes."""
    if func:
        return DEFAULT_REGISTRY.register_factory(func)
    else:
        def cb_method(func_2):
            return DEFAULT_REGISTRY.register_factory(func_2, **kwargs)
        return cb_method

