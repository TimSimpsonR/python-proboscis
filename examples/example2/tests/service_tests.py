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
from proboscis import SkipTest
from proboscis import test

db_config = {
    "url": "test.db.mycompany.com",
    "user": "service_admin",
    "password": "pass"
}


test_user = None


def generate_new_user_config():
    """Constructs the dictionary needed to make a new user."""
    new_user_config = {
        "username": "TEST_%s_%s" % (datetime.now(), random.randint(0, 256)),
        "password": "password",
        "type":"normal"
    }
    return new_user_config



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


@test(groups=["user", "service.tests"],
      depends_on=[initialize_web_server])
def create_user():
    random.seed()
    global test_user
    test_user = None
    new_user_config = generate_new_user_config()
    admin = mymodule.get_admin_client()
    test_user = admin.create_user(new_user_config)
    assert_equal(test_user.username, new_user_config["username"])
    assert_true(test_user.id is not None)
    assert_true(isinstance(test_user.id, int))


@test(groups=["user", "user.tests", "service.tests"],
      depends_on=[create_user])
def user_cant_connect_with_wrong_password():
    assert_raises(mymodule.UserNotFoundException, mymodule.login,
                  {'username':test_user.username, 'password':'fdgggdsds'})


@test(groups=["user", "user.tests", "service.tests"],
      depends_on=[create_user])
class WhenConnectingAsANormalUser(unittest.TestCase):

    def setUp(self):
        self.client = mymodule.login({
            'username':test_user.username, 'password':'password'})

    def test_auth_create(self):
        """Make sure the given client cannot perform admin actions.."""
        self.assertRaises(mymodule.AuthException, self.client.create_user,
                          generate_new_user_config())

    def test_auth_delete(self):
        """Make sure the given client cannot perform admin actions.."""
        self.assertRaises(mymodule.AuthException, self.client.delete_user,
                          test_user.id)

    def test_change_profile_image(self):
        """Test changing a client's profile image."""
        self.assertEquals("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        self.assertEquals("spam.jpg", self.client.get_profile_image())


@test(groups=["user", "service.tests"], depends_on_groups=["user.tests"],
      always_run=True)
def delete_user():
    if test_user is None:
        raise SkipTest("User tests were never run.")
    admin = mymodule.get_admin_client()
    admin.delete_user(test_user.id)
    assert_raises(mymodule.UserNotFoundException, mymodule.login,
                  {'username':test_user.username, 'password':'password'})


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

