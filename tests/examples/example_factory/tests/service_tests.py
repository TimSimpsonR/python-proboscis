"""
User service tests.

This is a test for a fictitious user web service which has rich client bindings
written in Python.

It assumes we have an existing test database which we can run the web service
against, using the function "mymodule.start_web_server()."

After spinning up the service, the test creates a new user and tests various
CRUD actions. Since its a test database, it is OK
to leave old users in the system but we try to always delete them if possible
at the end of the test.

"""

from proboscis import after_class
from proboscis import before_class
from proboscis import factory
from proboscis import test
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_is_none

from spam_api import create_admin_api
from spam_api import create_api
from spam_api import SpamHttpException


@test
class UserPermissionsTest(object):

    def __init__(self, config):
        self.user_type = config['user_type']
        self.create = config['create'] or None
        self.delete = config['delete'] or None
        self.read = config['read'] or None

    @before_class
    def create_user(self):
        self.admin_api = create_admin_api()
        user = self.admin_api.user.create(self.user_type)
        self.user_id = user.id
        self.api = create_api(self.user_id)

    @test
    def test_create(self):
        try:
            self.spam = self.api.spam.create()
            assert_is_none(self.create)
        except SpamHttpException as she:
            self.spam = self.admin_api.spam.create()
            assert_equal(she.status_code, self.create)

    @test(depends_on=[test_create])
    def test_read(self):
        try:
            spam = self.api.spam.get(self.spam.id)
            assert_is_none(self.read)
            assert_equal(spam, self.spam)
        except SpamHttpException as she:
            assert_equal(she.status_code, self.read)

    @test(depends_on=[test_create, test_read])
    def test_delete(self):
        try:
            self.api.spam.delete(self.spam.id)
            assert_is_none(self.delete)
        except SpamHttpException as she:
            assert_equal(she.status_code, self.delete)

    @after_class
    def delete_user(self):
        self.admin_api.user.delete(self.user_id)


@factory
def generate_user_tests():
    user_configs = [
        { 'user_type': "anonymous",
          'create':401, 'read':401, 'delete': 401 },
        { 'user_type': "restricted",
          'create':401, 'read':None, 'delete': 401 },
        { 'user_type': "normal",
          'create':None, 'read':None, 'delete': None }
    ]
    return [UserPermissionsTest(config) for config in user_configs]
