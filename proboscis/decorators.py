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

def expect_exception(exception_type):
    """Decorates a test method to show it expects an exception to be raised."""
    def return_method(method):
        def new_method(*kargs, **kwargs):
            try:
                method(*kargs, **kwargs)
                raise AssertionError("Expected exception of type " +
                                     str(exception_type))
            except exception_type:
                pass  # This is what we want
        return new_method
    return return_method


class TimeoutError(RuntimeError):
    """Thrown when a method has exceeded the time allowed."""
    pass


def time_out(time):
    """Raises TimeoutError if the decorated method does not finish in time."""
    def cb_timeout(signum, frame):
        raise TimeoutError("Time out after waiting " + str(time) + " seconds.")

    def return_method(func):
        """Turns function into decorated function."""
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


def decorate_class(setUp_method=None, tearDown_method=None):
    """Inserts method calls in the setUp / tearDown methods of a class."""
    def return_method(cls):
        """Returns decorated class."""
        new_dict = cls.__dict__.copy()
        if setUp_method:
            if hasattr(cls, "setUp"):
                def _setUp(self):
                    setUp_method(self)
                    cls.setUp(self)
            else:
                def _setUp(self):
                    setUp_method(self)
            new_dict["setUp"] = _setUp
        if tearDown_method:
            if hasattr(cls, "tearDown"):
                def _tearDown(self):
                    tearDown_method(self)
                    cls.setUp(self)
            else:
                def _tearDown(self):
                    tearDown_method(self)
            new_dict["tearDown"] = _tearDown
        return type(cls.__name__, (cls,), new_dict)
    return return_method
