import unittest
import mymodule
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_false
from proboscis.asserts import assert_true
from proboscis import factory, before_class, after_class
from proboscis import test

service_configs = [{
    "user_name":"bob",
    "pass_word":"pass_word"
},
{
    "user_name":"hub_cap",
    "pass_word":"booyahsucka"
},
{
    "user_name":"rnirmal",
    "pass_word":"p@ssw0rd"
}
]


@test(groups=["set_up"])
class SetUp(object):

    @test
    def create_database(self):
        """Setup... run before anything."""
        mymodule.create_database()
        assert_true(mymodule.tables_exist())

    @test
    def start_web_server(self):
        """Setup... run before anything."""
        mymodule.start_web_server()
        client = mymodule.ServiceClient(service_configs[0])
        assert_true(client.service_is_up)

@factory
def generate_client_tests():
    return [ClientTest(config) for config in service_configs]

#@test(depends_on=[SetUp]) #, depends_on_groups=['set_up'])
class ClientTest(object):

    def __init__(self, service_config):
        self.client = mymodule.ServiceClient(service_config)

    def test_change_profile_image(self):  #1
        """Factory # 1 - Test changing a client's profile image."""
        assert_equal("default.jpg", self.client.get_profile_image())
        self.client.set_profile_image("spam.jpg")
        assert_equal("spam.jpg", self.client.get_profile_image())

    def test_something_else(self):  #3
        """Factory # 3"""
        assert_equal(True, True)

    @test(depends_on=[test_change_profile_image],
          depends_on_groups=['before_one_more_thing'])
    def one_more_thing(self):  #2
        """Factory # 2 """
        assert_equal(True, True)

    test(depends_on=[test_change_profile_image, one_more_thing],
         groups=["something_else"])\
        (test_something_else)

    test(test_change_profile_image)

class BasicTest(object):

    def tearDown2(self):
        """BasicTest tearDown #2"""
        assert_true(True)

    @after_class
    def tearDown1(self):
        """BasicTest tearDown # 1"""
        assert_true(True)

    after_class(depends_on=[tearDown1])(tearDown2)


    @test(depends_on=[ClientTest])
    def do_something(self):
        """BasicTest-Run this after the factory methods, before after_cls."""
        assert_true(True)

    def setUp2(self):
        """BasicTest setUp. #2"""
        assert_true(True)

    @before_class
    def setUp1(self):
        """BasicTest setUp. #1"""
        assert_true(True)

    before_class(depends_on=[setUp1])(setUp2)

@test(depends_on=[ClientTest, BasicTest])
def after_cls():
    """after_cls - Run this after the factory methods and BasicTest."""
    assert_true(True)



test(depends_on=[SetUp])(ClientTest)
test(depends_on=[SetUp])(BasicTest)


@test(depends_on_groups=["something_else"], groups=["normal"])
def sometime_later():
    """Run this after the factory method #3."""
    assert_true(True)

@test(groups=["before_one_more_thing"])
def sometime_before():
    """Run this before factory method #2."""
    assert_true(True)



@test(depends_on=[ClientTest],
      depends_on_groups=['normal'], always_run=True)
class ShutDown(object):

    @test
    def test_stop_service(self):
        """Shut down the web service."""
        client = mymodule.ServiceClient(service_configs[0])
        if client.service_is_up:
            mymodule.stop_web_server()
            assert_false(client.service_is_up())

    @test
    def test_destroy_database(self):
        """Destroy the local database."""
        mymodule.destroy_database()