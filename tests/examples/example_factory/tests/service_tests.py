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

from datetime import datetime
import random
import types
import unittest
import mymodule
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_raises
from proboscis.asserts import assert_true
from proboscis import after_class
from proboscis import before_class
from proboscis import SkipTest
from proboscis import test

db_config = {
    "url": "test.db.mycompany.com",
    "user": "service_admin",
    "password": "pass"
}



@test
def initialize_database():
    """Creates a local database."""
    mymodule.create_database()
    assert_true(mymodule.tables_exist())

@test(depends_on=[initialize_database])
def initialize_web_server():
    """Starts up the web service."""
    mymodule.start_web_server()
    admin = mymodule.get_admin_client()
    assert_true(admin.service_is_up)


class UserTests(object):

    def __init__(self, user_type):
        self.expected_user_type = user_type

    def generate_new_user_config(self):
        """Constructs the dictionary needed to make a new user."""
        new_user_config = {
            "username": "TEST_%s_%s" % (datetime.now(), random.randint(0, 256)),
            "password": "password",
            "type":self.expected_user_type
        }
        return new_user_config

    @before_class
    def create_user(self):
        """Create a user."""
        random.seed()
        global test_user
        test_user = None
        new_user_config = self.generate_new_user_config()
        admin = mymodule.get_admin_client()
        self.test_user = admin.create_user(new_user_config)
        assert_equal(self.test_user.username, new_user_config["username"])
        assert_true(self.test_user.id is not None)
        assert_true(isinstance(self.test_user.id, (types.IntType,
                                                   types.LongType)))

    @after_class(always_run=True)
    def delete_user(self):
        if self.test_user is None:
            raise SkipTest("User tests were never run.")
        admin = mymodule.get_admin_client()
        admin.delete_user(self.test_user.id)
        assert_raises(mymodule.UserNotFoundException, mymodule.login,
                    {'username':self.test_user.username, 'password':'password'})

    def cant_login_with_wrong_password(self):
        assert_raises(mymodule.UserNotFoundException, mymodule.login,
                      {'username':self.test_user.username, 'password':'blah'})

    @test
    def successful_login(self):
        self.client = mymodule.login({
            'username':self.test_user.username, 'password':'password'})

    @test(depends_on=[successful_login])
    def change_profile_image(self):
        """Test changing a client's profile image."""
        assert_equal("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        assert_equal("spam.jpg", self.client.get_profile_image())


    @test(depends_on=[successful_login])
    def create_users(self):
        """Make sure the given client cannot perform admin actions.."""
        if self.expected_user_type == 'normal':
            assert_raises(mymodule.AuthException, self.client.create_user,
                          self.generate_new_user_config())
        else:
            pass


    @test(depends_on=[successful_login])
    def delete_users(self):
        """Make sure the given client cannot perform admin actions.."""
        assert_raises(mymodule.AuthException, self.client.delete_user,
                      self.test_user.id)



@factory
def generate_user_tests():
    return [ClientTest(config) for config in service_configs]





@test(groups=["user", "service.tests"])
class AdminUserTests(UserTests):

    @staticmethod
    def generate_new_user_config():
        """Constructs the dictionary needed to make a new user."""
        new_user_config = {
            "username": "TEST_%s_%s" % (datetime.now(), random.randint(0, 256)),
            "password": "password",
            "type":"admin"
        }
        return new_user_config

    @test(depends_on=[UserTests.successful_login])
    def an_admin_user_can_create_users(self):
        """Make sure the given client cannot perform admin actions.."""
        self.new_user = self.client.create_user(self.generate_new_user_config())
        # Make sure it actually logs in.
        self.new_user_client = mymodule.login({
            'username':self.new_user.username, 'password':'password'})

    @test(depends_on=[an_admin_user_can_create_users])
    def an_admin_user_can_delete_users(self):
        """Make sure the given client cannot perform admin actions.."""
        self.client.delete_user(self.new_user.id)


# Add more tests in the service.tests group here, or in any other file.
# Then when we're finished...

@test(groups=["service.shutdown"], depends_on_groups=["service.tests"],
      always_run=True)
def shut_down():
    """Shut down the web service and destroys the database."""
    admin = mymodule.get_admin_client()
    if admin.service_is_up:
        mymodule.stop_web_server()
        assert_false(admin.service_is_up())
    mymodule.destroy_database()

