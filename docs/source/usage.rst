Usage
=================

Writing Tests
-------------

Proboscis runs imported test functions or classes decorated with the
proboscis.test decorator.  Decorated classes extending unittest.TestCase run
exactly like they do in Nose / unittest.

This means traditional Python unit test classes can run as-is in Proboscis
provided they are decorated.

For example:

.. include:: ../build/examples/unit/source/tests/unit.py

Proboscis exists to provide a foundation for high-level testing in custom
test harnesses so unlike Nose all tests modules must be imported directly in
code, and using it requires you write a start-up script like the following:

.. include:: ../build/examples/unit/source/run_tests.py

Assuming this is named something like "run_test.py" you can run it like so:

.. include:: ../build/examples/unit/output/output.rst


Proboscis is more useful for higher level tests which may have dependencies on
each other or need to run in a guaranteed order.

Nose can order tests based on their placement and name but the effect is
difficult to maintain, especially when working with multiple modules.
Additionally, if one test performs some sort of initialization to produce a
state required by other tests and fails, the dependent tests run despite
having no chance of succeeding. These additional failures pollute the results
making the true problem harder to see.

In Proboscis, if one tests depends on another which fails, the
dependent test raises SkipTest automatically, making it easier to track down
the real problem.

For example:

.. include:: ../build/examples/example1/source/tests/service_tests.py

This code models an end user hitting a web service to change his profile
pictures.

To do this without mocking anything, it has to set up a local
database instance and  start the actual web service.  This is done in the
group marked "service.initialization." Because the "service.tests" group
depends on it, those tests can assume that the services are up.

Additionally, if the initialization phase fails somehow it will
be represented like any other test, and all tests in the integration.tests
group will be marked as "skip" instead of fail.

When the tests are finished the group "integration.shutdown" runs.  The two
test classes in this group are marked as  "never_skip", which prevents them
from not running if anything in the "integration.tests" group fails but still
causes them to run afterwards.

.. include:: ../../README
   :start-line: 59
   :end-line: 62

Of course, whether or not its worth it to start the real database and the web
service or if the tests instead should use mocks depends on the particulars of
the application and the religion of the test author.

Running Proboscis
-----------------

Proboscis doesn’t have a standard script and can't automatically load modules
in a directory, so you have to import them programmatically manually before passing control to Proboscis.

Proboscis requires test modules to be imported manually and any project
using it will need to write its own main test script.  Don't worry though
because this is pretty easy.  Such a script is also normally a good place
to specify additional bits of configuration or organization.

Here's an example:

.. include:: ../build/examples/example1/source/run_tests.py

The constructor of the class proboscis.TestProgram sorts and filters the test
suite (using the command line arguments as described below) on creation.  Be
warned that it should only be called once- calling it multiple times will lead
to strange behavior.

The method "run_and_exit" passes control to nose.core.TestProgram
(which passes control to the unittest module) and exits the program.
By default, proboscis.TestProgram reads arguments from sys.argv.
Assuming this script was named runtests.py, you'd could run all the tests
using this command:

.. code-block:: bash

    python runtests.py

...run just the unit tests with this one:

.. code-block:: bash

    python runtests.py --group=unit

...or run all the slow tests:

.. code-block:: bash

    python runtests.py --group=slow

You can see how Proboscis will order the tests using the --show-plan option.

.. code-block:: bash

    python runtests.py --groups=slow --show-plan


