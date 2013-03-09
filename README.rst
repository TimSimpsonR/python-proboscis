Proboscis
================

Proboscis is a Python test framework that extends Python's built-in unittest
module and `Nose`_ with features from `TestNG`_.

.. _Nose: http://readthedocs.org/docs/nose/en/latest/

.. _TestNG: http://testng.org/doc/index.html

`Click here to read the full docs`_.

.. _`Click here to read the full docs`: http://packages.python.org/proboscis/


Features
--------

- Uses decorators instead of naming conventions.

- Allows for TestNG style test methods, in which a class is initialized once,
  as an alternative to using class fields (see the example below).

- Allows for explicit `test dependencies`_ and skipping of dependent tests
  on failures.

- Runs xUnit style clases if desired or needed for backwards compatability.

- Uses Nose if available (but doesn't require it), and works with many of its
  plugins.

- Runs in `IronPython`_ and `Jython`_ (although if you're targetting the JVM
  you should consider using TestNG instead)!

.. _`test dependencies`: http://beust.com/weblog/2004/08/18/using-annotation-inheritance-for-testing/
.. _IronPython: http://ironpython.net/
.. _Jython: http://www.jython.org/



Updates
-------

Version 1.2.6.0
~~~~~~~~~~~~~~~

- Proboscis now works with Python 3!

Version 1.2.5.3
~~~~~~~~~~~~~~~

- Fixed bug in runs_after_groups inheritance.
- Allow "import *" from proboscis asserts.

Version 1.2.5.2
~~~~~~~~~~~~~~~

- Fixed a bug that prevented some Nose plugins from working.

Version 1.2.5.1
~~~~~~~~~~~~~~~

- Implemented test decorator property "runs_after", which affects only the
  order of test runs. If a test noted by "runs_after" fails, the test method
  or class targeted by the decorator will *not* be skipped. If a group is run,
  tests which are listed in "runs_after" will not implicitly be run as well.
- Added 'fail' method to Checker class.
- Using tox discovered some issues with Jython compatability.

Version 1.2.4
~~~~~~~~~~~~~

- Added a missing parameter to a format string error message.
- Fixed bug where the enabled property was not being inherited by class methods.
- Added a Check class to allow testing multiple assertions in a with block.


Example
-------

This example tests an external web service by creating an admin user and
updating the profile picture.

::

    @test(groups=["service.initialization"])
    def make_sure_service_is_up():
        # No point in proceeding if the service isn't responding.
        assert_true(service_module.ping(service_config))


    @test(groups=["service.tests"], depends_on_groups=["service.initialization"])
    class AdminTest(object):

        @before_class
        def create_admin_user(self):
            self.client = service_module.ServiceClient(service_config)
            self.admin = self.client.create_admin_user("boss")

        @test
        def check_for_defaults(self):
            assert_equals("default.jpg", self.admin.get_profile_image())

        @test(depends_on=check_for_defaults)
        def change_picture(self):
            self.admin.set_profile_image("spam.jpg")
            assert_equals("spam.jpg", self.admin.get_profile_image())

        # Put other tests against admin user here...

        @after_class
        def destroy_admin_user(self):
            self.client.delete_user(self.admin)



Here, the variable "admin" is created only once, similar to TestNG.

If the xUnit style is preferred or needed for backwards compatability the
following code will create the admin variable once for each test function:

::

    @test(groups=["service.tests"], depends_on_groups=["service.initialization"])
    class AdminTest(unittest.TestCase):

        def setUp(self):
            self.client = service_module.ServiceClient(service_config)
            self.admin = self.client.create_admin_user("boss")

        def test_change_picture(self):
            assert_equals("default.jpg", self.admin.get_profile_image())
            self.admin.set_profile_image("spam.jpg")
            assert_equals("spam.jpg", self.admin.get_profile_image())

        # Put other tests against admin user here...

        def tearDown(self):
            self.client.delete_user(self.admin)

Though this version of AdminTest runs like an xUnit test, it still runs after
the "service.initialization" group.

For more info see the `full docs`_.

.. _`full docs`: http://packages.python.org/proboscis/
