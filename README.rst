=========
Proboscis
=========

Proboscis brings TestNG features to Python while being built on top of and
backwards-compatible with Python's built-in unittest module.

`View the generated docs here.`__

__http://packages.python.org/proboscis/

.. contents::
   :local:

Summary
-------
Proboscis uses decorators similar to TestNG's annotations instead of naming
conventions to mark classes and
functions as tests. If a class is decorated with proboscis.test, a single
instance of the class is created and used to run all decorated methods, similar
to TestNG. However, if the decorated class extends unittest.TestCase it is run
using the traditional rules.

Like TestNG, Proboscis allows tests to be added to groups so they can be
organized and run independently of the code layout (similar to tags in Nose).
It also
lets tests cleanly and explicitly declare dependencies on other tests, opening
the door for functional and integration testing (if you are maintaining Python
tests which use funny names like "010_start", "020_connect", etc. or find that
everything breaks when you try to move a module to a different package, you're
running tests like this now and need to be using a tool that supports them).
Of course, Proboscis works fine for unit testing as well.

Proboscis also supports factory methods, which operate similar to those in
TestNG.

Proboscis will use Nose instead of the unittest module if it is available;
otherwise, it uses only the core Python libraries so that it can also run on
Iron Python and Jython. Some Nose plugins work with Proboscis out of the box,
while others may take some prodding or not work at all. Proboscis works only
in Python 2, but Python 3 support is pending.


Updates
-------
Version 1.2.4
* Added a missing parameter to a format string error message.
* Fixed bug with enabled property not being inherited by class methods.
* Added a Check class to allow testing multiple assertions in a with block.

Version 1.2.3
* Proboscis is now compatable with IronPython and the JVM!


Example
-------

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

A more advanced tutorial is available in the generated docs.

