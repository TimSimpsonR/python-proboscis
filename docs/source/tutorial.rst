Tutorial
=================

Writing Unit Tests
------------------

Proboscis runs imported test functions or classes decorated with the
proboscis.test decorator.  Decorated classes extending unittest.TestCase run
exactly like they do in Nose / unittest.

This means traditional Python unit test classes can run as-is in Proboscis
provided they are decorated.

For example:

.. include:: ../build/examples/unit/source/tests/unit.py
   :end-line: 20

You can also attach the proboscis.test decorator to functions to run them
by themselves:

.. include:: ../build/examples/unit/source/tests/unit.py
   :start-line: 20

Unlike Nose Proboscis requires all tests modules must be imported directly in
code, so using it requires you write a start-up script like the following:

.. include:: ../build/examples/unit/source/run_tests.py

Assuming this is named something like "run_test.py" you can run it like so:

.. include:: ../build/examples/unit/output/output0.rst


TestProgram.run_and_exit() expects to be used in scripts like this and takes
command line arguments into account (Note: it's called "run_and_exit()"
because to run the tests it calls Nose which then calls unittest, which calls
sys.exit() on completion and forces the program to exit).

Normally, all tests are run, but we can use the "--group" command line
parameter to run only a certain group (and the groups it depends on)
instead:

.. include:: ../build/examples/unit/output/output1.rst

If you want to run multiple specific groups, use the "--group"
parameter more than once.

You can also use the "--show-plan" argument to get a preview of how Proboscis
will run the tests:

.. include:: ../build/examples/unit/output/output2.rst

Unused arguments get passed along to Nose or the unittest module, which means
its possible to run some plugins designed for them. However,
Proboscis is by nature invasive and intentionally and unintentionally breaks
certain features of Nose and unittest (such as test discovery) so your
mileage may vary.

Writing Higher Level Tests
--------------------------

Proboscis is more useful for higher level tests which may have dependencies on
each other or need to run in a guaranteed order.

Nose can order tests lexically but the effect is
difficult to maintain, especially when working with multiple modules.
Additionally, if one test performs some sort of initialization to produce a
state required by other tests and fails, the dependent tests run despite
having no chance of succeeding. These additional failures pollute the results
making the true problem harder to see.

In Proboscis, if one tests depends on another which fails, the
dependent test raises Nose's SkipTest or calls unittest's skipTest()
automatically, making it easier to track down the real problem. If neither
feature is available (as is the case with Python 2.5), it simply raises an
assertion with a message beginning with the word "SKIPPED."

The following example shows how to write a test with dependencies to test a
fictitious web service that stores user profiles. The service allows admin
users to create and delete users and allows users to edit a profile picture.

.. include:: ../build/examples/example1/source/tests/service_tests.py

Our initialization code runs in three phases: first, we create the database,
second, we start the web service (assuming its some kind of daemon we can
run programmatically) and third we create a new user. The function
"initialize_database_and_server" is in the group
"service.initialization", while the function "create_user" is in the group
"user.initialization". Note that the "create_user" depends on
"initialize_database_and_server", so Proboscis guarantees it runs after.

The meat of the test is where we run some operations against the user. These
classes and functions are marked as depending on the "user.initialization"
group and so run later.

The tests which clean everything up depend on the groups "user.tests" and
"service.tests" respectively. We also set the "always_run" property to true so
that if a test in the group they depend on fails they will still run. Since
the "delete_user" test function could run even when the "create_user" test
function fails to even make a user, we add some code to check the status of the
global "test_user" object and skip it if it was never set.

When we run the run_test.py script, we see everything is ordered correctly:

.. include:: ../build/examples/example1/output/output0.rst

In some frameworks initialization code is run as part of a "fixture", or
something else which is a bit different than a test, but in Proboscis our
initialization code is a test itself and can be covered with assertions.

Let's say there's an error and the web service starts up. In a traditional
testing framework, you'd see a stream of error messages as every test failed.
In Proboscis, you get this:

.. include:: ../build/examples/example1/output/output1.rst


Ordering tests without groups
-----------------------------

The example above is pretty group heavy- in some cases, a group is created
just to establish a single dependency.

Its also possible to establish dependencies without groups by listing a
function or class directly as a dependencies. The code below runs identically to
the example above but does so without groups:

.. include:: ../build/examples/example2/source/tests/service_tests.py


Using TestNG style test methods to factor out global variables
--------------------------------------------------------------

The example above creates the test user as a global variable so it can pass it
between the tests which use it. Because unittest creates a new instance of
the class "WhenConnectingAsANormalUser" for each method it runs, we can't
run the code to create the user in the setUp method and store it in that class
either.

An gross alternative would be to merge all of the
tests which require a user into a single function, but this would understandably
be a bit gross. It also would not be equivalent, since if one test failed,
no other tests would get a chance to run (for example, if test represented by
"test_auth_delete" unittest would output a single test failure, and the test
for "change_profile_image" would never run). It would also be uncharitable to
anyone who had to maintain the code.

There's another way in Proboscis, though, which is to run test methods in the
style of TestNG by putting the @test decorator on both the class and test
methods and making sure the class does not extend unittest.TestCase.

When the TestNG method is used, a single instance of a class is created and
used to run each method.

If we do this, we can combine all of the tests which require the user into
one class as follows:

.. include:: ../build/examples/example3/source/tests/service_tests.py

@before_class and @after_class work just like the @test decorator and accept
the same arguments, but also tell the method to run either before and after all
other methods in the given class.

If a test can fit into one class, its usually best to write it this way.

Consider what happens if we want to test the admin user- before, we would have
had to duplicate our test code for the normal user or somehow gotten the
same test code to run twice while we altered the global test_user variable
in between.

However using the newly refactored code testing for the admin user can be
accomplished fairly easy via subclassing:

.. include:: ../build/examples/example4/source/tests/service_tests.py




Additional Tricks
-----------------

Groups of Groups
~~~~~~~~~~~~~~~~

Its possible to create empty test entries that link groups together using the
proboscis.register function without a class or function.  A good
place to do (as well as store other bits of configuration) is in the start up
script you write for Proboscis.  Here's an example:

.. include:: ../build/examples/example1/source/run_tests.py

Here the groups "fast", "integration", and "slow" are created as simple
dependencies on other groups.  This makes it possible to, for example, run
all "slow" tests with the following command:

.. code-block:: bash

    python runtests.py --group=slow

