# Copyright (c) 2012 Rackspace
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

"""Like asserts, but does not raise an exception until the end of a block."""

import traceback
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_not_equal
from proboscis.asserts import ASSERTION_ERROR


def get_stack_trace_of_caller(level_up):
    """Gets the stack trace at the point of the caller."""
    level_up += 1
    st = traceback.extract_stack()
    caller_index = len(st) - level_up
    if caller_index < 0:
        caller_index = 0
    new_st = st[0:caller_index]
    return new_st


class Checker(object):

    def __init__(self):
        self.messages = []
        self.odd = True
        self.protected = False

    def _add_exception(self, _type, value, tb):
        """Takes an exception, and adds it as a string."""
        if self.odd:
            prefix = "* "
        else:
            prefix = "- "
        start = "Check failure! Traceback:"
        middle = prefix.join(traceback.format_list(tb))
        end = '\n'.join(traceback.format_exception_only(_type, value))
        msg = '\n'.join([start, middle, end])
        self.messages.append(msg)
        self.odd = not self.odd

    def equal(self, *args, **kwargs):
        self._run_assertion(assert_equal, *args, **kwargs)

    def false(self, *args, **kwargs):
        self._run_assertion(assert_false, *args, **kwargs)

    def not_equal(self, *args, **kwargs):
        _run_assertion(assert_not_equal, *args, **kwargs)

    def _run_assertion(self, assert_func, *args, **kwargs):
        """
        Runs an assertion method, but catches any failure and adds it as a
        string to the messages list.
        """
        if self.protected:
            try:
                assert_func(*args, **kwargs)
            except ASSERTION_ERROR as ae:
                st = get_stack_trace_of_caller(2)
                self._add_exception(ASSERTION_ERROR, ae, st)
        else:
            assert_func(*args, **kwargs)

    def __enter__(self):
        self.protected = True
        return self

    def __exit__(self, _type, value, tb):
        self.protected = False
        if len(self.messages) == 0:
            final_message = None
        else:
            final_message = '\n'.join(self.messages)
        if _type is not None:  # An error occurred
            if len(self.messages) == 0:
                raise _type, value, tb
            self._add_exception(_type, value, traceback.extract_tb(tb))
        if len(self.messages) != 0:
            final_message = '\n'.join(self.messages)
            raise ASSERTION_ERROR(final_message)

    def true(self, *args, **kwargs):
        self._run_assertion(assert_true, *args, **kwargs)
