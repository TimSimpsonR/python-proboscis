import unittest
import mymodule
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_true
#from proboscis import before_class
from proboscis import test

service_config = {
    "user_name":"bob",
    "pass_word":"pass_word"
}

@test
class SetUp(object):

    @test(groups=['setup'])
    def create_database(self):
        """Creates a local database."""
        mymodule.create_database()
        assert_true(mymodule.tables_exist())
        #assert_true(False)

    @test(groups=['setup'])
    def start_web_server(self):
        """Start up web server then issue a connect to make sure its up."""
        mymodule.start_web_server()
        client = mymodule.ServiceClient(service_config)
        assert_true(client.service_is_up)


@test(groups=['normal'])
class WhenConnectingAsAdmin(object):

    #TODO: before_class
    def __init__(self):
        self.client = mymodule.ServiceClient(service_config)

    @test(groups=["a"], depends_on_groups=["setup"])
    def test_has_credentials(self):
        """Make sure the given client has ADMIN access."""
        assert_equal(self.client.check_credentials,
                     mymodule.ServiceClient.ADMIN)

    @test(groups=['c'], depends_on_groups=["setup", 'b'])
    def test_change_profile_image(self):
        """Test changing a client's profile image."""
        assert_equal("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        assert_equal("spam.jpg", self.client.get_profile_image())


# Add more tests in the service.tests group here, or in any other file.
# Then when we're finished...

@test
class SomethingElse(object):

    def __init__(self):
        self.bee = 1

    @test(groups=['d'], depends_on_groups=["c"])
    def whatever(self):
        self.bee += 1
        assert_equal(self.bee, 3)

    @test(groups=['b'], depends_on_groups=["a"])
    def something_else(self):
        self.bee += 1
        assert_equal(self.bee, 2)


@test(depends_on=[WhenConnectingAsAdmin],
      depends_on_groups=['normal'], always_run=True)
class ShutDown(object):

    @test
    def test_stop_service(self):
        """Shut down the web service."""
        client = mymodule.ServiceClient(service_config)
        if client.service_is_up:
            mymodule.stop_web_server()
            assert_false(client.service_is_up())

    @test
    def test_destroy_database(self):
        """Destroy the local database."""
        mymodule.destroy_database()