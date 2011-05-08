import unittest
import mymodule
from proboscis import register
from proboscis import test

service_config = {
    "user_name":"bob",
    "pass_word":"pass_word"
}

@test(groups=["service.initialization"])
class CreateDatabase(unittest.TestCase):
    """Creates a local database."""

    def test_create(self):
        mymodule.create_database()
        self.assertTrue(mymodule.tables_exist())

@test(groups=["service.initialization"])
class StartWebServer(unittest.TestCase):
    """Starts the web server."""

    def test_start(self):
        # Start up web server then issue a connect to make sure its up.
        mymodule.start_web_server()
        client = mymodule.ServiceClient(service_config)
        self.assertTrue(client.service_is_up)

register(groups=["service.tests"],
         depends_on_groups=["service.initialization"])

@test(groups=["service.tests"])
class WhenConnectingAsAdmin(unittest.TestCase):

    def setUp(self):
        self.client = mymodule.ServiceClient(service_config)

    def test_has_credentials(self):
        self.assertEqual(self.client.check_credentials,
                         mymodule.ServiceClient.ADMIN)

    def test_change_profile_image(self):
        self.assertEquals("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        self.assertEquals("spam.jpg", self.client.get_profile_image())

# Add more tests in the service.tests group here, or in any other file.
# Then when we're finished...

register(groups=["service.shutdown"],
         depends_on_groups=["service.tests"])
@test(groups=["service.shutdown"], never_skip=True)
class StopService(unittest.TestCase):

    def test_stop(self):
        client = mymodule.ServiceClient(service_config)
        if client.service_is_up:
            mymodule.stop_web_server()
            self.assertFalse(client.service_is_up())


@test(groups=["service.shutdown"], never_skip=True)
class DestroyDatabase(unittest.TestCase):

    def test_stop(self):
        mymodule.destroy_database()