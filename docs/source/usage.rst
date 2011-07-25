Usage
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

.. include:: ../build/examples/unit/output/output1.rst


TestProgram.run_and_exit() expects to be used in scripts like this and takes
command line arguments into account (Note: it's called "run_and_exit()"
because to run the tests it calls Nose which then calls unittest, which calls
sys.exit() on completion and forces the program to exit).

Normally, all tests are run, but we can use the "--group" command line
parameter to run only tests in a certain groups run instead:

.. include:: ../build/examples/unit/output/output2.rst

You can also use the "--show-plan" argument to get a preview of how Proboscis
will run the tests:

.. include:: ../build/examples/unit/output/output3.rst

Unused arguments get passed along to Nose. However, Proboscis is by nature
invasive and intentionally and unintentionally breaks many Nose features so
most of them won't work well or at all.

It is worth noting that the ability to organize tests into groups is present
in Nose via the "attr" decorator.

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
dependent test raises SkipTest automatically, making it easier to track down
the real problem.

For example, lets say we're testing a web service that allows a user to store
and change their profile pictures which come from a database.

To test this without mocking anything, we need to set up a local
database instance and  start the actual web service.  However, if this code
is tricky enough it may be a test in its own right.

In Proboscis we can actually make the initialization code a test and put it
in a group marked "service.initialization." The tests which depend on the
initialization procedure which we actually care about are put in a group called
"service.tests". Finally, we can make a third group responsible for shutting
down the web service and database and call it "service.shutdown." If this
group is dependent on the "service.tests" group it won't run until after all
of the other tests.

Here's what the code looks like:

.. include:: ../build/examples/example1/source/tests/service_tests.py

.. include:: ../build/examples/example1/output/output0.rst

If the initialization phase fails somehow it will
be represented like any other test, and all tests in the integration.tests
group will be marked as "skip" instead of fail:

.. include:: ../build/examples/example1/output/output1.rst

When the tests are finished the group "integration.shutdown" runs.  The two
test classes in this group are marked as  "always_run", which prevents them
from not running if anything in the "service.tests" group fails but still
causes them to run afterwards.

.. include:: ../../README
   :start-line: 59
   :end-line: 62

Of course, whether or not its worth it to start the real database and the web
service or if the tests instead should use mocks depends on the particulars of
the application and the religion of the test author.

Its also possible to declare that a test declares on another class or function
using the "depends_on" argument.  So the file above could be written like so:

.. include:: ../build/examples/example2/source/tests/service_tests.py


Additional Tricks
-----------------

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
