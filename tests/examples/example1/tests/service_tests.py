import unittest
import mymodule
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_true
from proboscis import test

service_config = {
    "user_name":"bob",
    "pass_word":"pass_word"
}

@test(groups=["service.initialization"])
def create_database():
    """Creates a local database."""
    mymodule.create_database()
    assert_true(mymodule.tables_exist())

@test(groups=["service.initialization"])
def start_web_server():
    """Start up web server then issue a connect to make sure its up."""
    mymodule.start_web_server()
    client = mymodule.ServiceClient(service_config)
    assert_true(client.service_is_up)


@test(groups=["service.tests"], depends_on_groups=["service.initialization"])
class WhenConnectingAsAdmin(unittest.TestCase):

    def setUp(self):
        self.client = mymodule.ServiceClient(service_config)

    def test_has_credentials(self):
        """Make sure the given client has ADMIN access."""
        self.assertEqual(self.client.check_credentials,
                         mymodule.ServiceClient.ADMIN)

    def test_change_profile_image(self):
        """Test changing a client's profile image."""
        self.assertEquals("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        self.assertEquals("spam.jpg", self.client.get_profile_image())


# Add more tests in the service.tests group here, or in any other file.
# Then when we're finished...


@test(groups=["service.shutdown"],
           depends_on_groups=["service.initialization", "service.tests"],
           always_run=True)
def stop_service():
    """Shut down the web service."""
    client = mymodule.ServiceClient(service_config)
    if client.service_is_up:
        mymodule.stop_web_server()
        assert_false(client.service_is_up())


@test(groups=["service.shutdown"],
           depends_on_groups=["service.initialization", "service.tests"],
           always_run=True)
def destroy_database():
    """Destroy the local database."""
    mymodule.destroy_database()