=========
Proboscis
=========

An extension for Nose that facilitates higher level testing.

Changes how test classes are discovered by forcing them to register via
decorators which contain useful metadata such as what groups they are in,
whether or not they have dependencies on other tests, and if they should be
ignored.

Proboscis sorts all registered tests into the desired run order then
constructs a test suite which it passes to Nose.  It can also filter this list
so that it's possible to specify which groups of tests you wish to run without
passing in the exact test classes.  At runtime, tests which depend on other
tests that have failed are automatically marked as skipped.

Much of this functionality was "inspired" by TestNG.  If you're coming from
that framework, the main features Proboscis currently offers are dependent test
ordering and the ability to arrange tests into groups independent of the
structure of their modules or packages.

With Proboscis it's possible to write tests which depend on a web service
(or some other dependency you'd like to only initialize once) like this:

    @test(groups=["service.tests"], depends_on_groups=["service.initialization"])
    class WhenConnectingAsAdmin(unittest.TestCase):

        def test_change_profile_image(self):
            self.client = mymodule.ServiceClient(service_config)
            self.assertEquals("default.jpg", self.client.get_profile_image())
            self.client.set_profile_image("spam.jpg")
            self.assertEquals("spam.jpg", self.client.get_profile_image())

Then write the code to start and cleanly shut down that web service in any other
module as a first class test itself:

    @test(groups=["service.initialization"])
    class StartWebServer(unittest.TestCase):

        def test_start(self):
            # Start up web server, then issues a connect.
            mymodule.start_web_server()
            client = mymodule.ServiceClient(service_config)
            self.assertTrue(client.service_is_up)

    @test(groups=["service.shutdown"], \
          depends_on_groups=["service.initialization", "service.tests"], \
          always_run=True)
    class StopService(unittest.TestCase):

        def test_stop(self):
            client = mymodule.ServiceClient(service_config)
            if client.service_is_up:
                mymodule.stop_web_server()
                self.assertFalse(client.service_is_up())

Using Proboscis you can rest assured the tests will execute in the desired
order even if you add more test classes, change their name, or move them
to different modules.
