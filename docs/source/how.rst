How it works
------------

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
