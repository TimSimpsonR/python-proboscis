"""

This mess runs the documentation examples to make sure they actually work.
It isn't easy because it has to use Python's reload mechanics since Proboscis
isn't currently designed to be run multiple times.

The tests run here can be run more easily from the command line by entering
into the various subdirectories of tests/examples and running the following
commands in Linux (its basically the same in Windows with the usual changes):

    Python:
        PYTHONPATH=../../../ python run_tests.py
    Jython:
        JYTHONPATH=../../../ jython run_tests.py


These are basically the higher order tests for Proboscis. Some unit tests
are in tests/proboscis_test.py.

"""
import os
import sys

from proboscis.asserts import assert_equal
from os.path import join

import proboscis
from proboscis.compatability import capture_exception
from proboscis.compatability import is_jython
from proboscis.compatability import reload


CAN_USE_WITH = not is_jython()


def fake_exit(*args, **kwargs):
    pass

def make_dirs(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def reload_proboscis():
    """
    Reloading Proboscis like this causes problems- for instance,
    exceptions aren't caught because the exception to be caught is a
    an earlier version of the reloaded doppleganger that is thrown.
    """
    reload(proboscis)
    def new_cap_ex(body_func, except_type):
        e = capture_exception(body_func, Exception)
        if e:
            if (str(type(e)) == str(except_type)):
                return e
            else:
                raise
        return None
    proboscis.compatability.capture_exception = new_cap_ex

class FailureLines(object):
    """Tallies expected and actual occurrences of lines in output."""

    def __init__(self, source_file, lines):
        self.source_file = source_file
        self.failures = {}
        for line in lines:
            self.add_expected(line)

    def add_actual(self, line):
        self.get(line)["actual"] += 1

    def add_expected(self, line):
        self.get(line)["expected"] += 1

    def assert_all(self):
        for key in self.failures.keys():
            self.assert_line(key)

    def assert_line(self, line):
        info = self.get(line)
        assert_equal(str(info["expected"]).strip(),
                     str(info["actual"]).strip(),
                "In %s, expected to see failure for \"%s\" %d time(s) but saw "
                "it %d time(s).  Additional info for this test: %s" %
                (self.source_file, line, info["expected"], info["actual"],
                 str(self.failures)))

    def get(self, line):
        if line not in self.failures:
            self.failures[line] = {"expected":0, "actual":0}
        return self.failures[line]


def assert_failures_in_file(source_file, expected_failures):
    """Checks the output of Proboscis run for expected failures."""
    failures = FailureLines(source_file, expected_failures)
    # Iterate the output, find all lines of text with the words FAIL or ERROR
    # and add them to a collection of "actual" failures that can be checked
    # against expected failures.
    # 2.7 seems to put the important parts on the next line, while 2.6 has it
    # on the same line.
    # I think Nose may also use this first format.
    if is_jython() or sys.version_info < (2, 7) \
        or proboscis.dependencies.use_nose:
        for line in open(source_file, 'r'):
            if "FAIL: " in line:
                failures.add_actual(line[6:].strip())
            elif "ERROR: " in line:
                failures.add_actual(line[7:].strip())
    else:
        error_next = False
        for line in open(source_file, 'r'):
            if error_next:
                failures.add_actual(line.strip())
            error_next = False
            if "ERROR: " in line or "FAIL: " in line:
                error_next = True
    failures.assert_all()


def create_rst(block_type, source_file, rst_file):
    """Converts Python files into a .rst files in the docs/build directory."""
    print(source_file + " ---> " + rst_file)
    if not os.path.exists(source_file):
        raise ValueError("File %s not found." % source_file)
    make_dirs(os.path.dirname(rst_file))
    output = open(rst_file, 'w')
    try:
        def code_block():
            output.write(".. code-block:: " + block_type + "\n\n")
        code_block()
        for line in open(source_file, 'r'):
            if line.strip() == "#rst-break":
                code_block()
            else:
                output.write("    " + line)
    finally:
        output.close()

class ExampleRunner(object):
    """Runs an example folder as if Python was executed from that directory.

    Also converts all source code into .rst files which can be easily consumed
    by the docs. In order to act as if Python was executed from a different
    directory, it has to do nasty things to the path. In order to run through
    Proboscis (and especially unittest.TestProgram, which Proboscis and Nose
    call) multiple times it has to muck with the modules dictionary.

    """

    def __init__(self, root, test):
        """
        Runs an example, which contains a base_directory relative to
        tests/examples, a list of source files in that directory (for .rst
        conversion) and a series of elements describing the different ways to
        "run" the example (this is to show examples of how to invoke Proboscis
        in the docs).
        """
        self.test = test
        self.base_directory = join(root, "docs", "build", "examples",
                                   test.base_directory)
        self.rst_directory = join(self.base_directory, "source")
        self.src_directory = join(root, "tests", "examples")

        self.create_rst_from_source()
        for (index, run_info) in enumerate(test.runs):
            self.run(run_info, index)

    def alter_argv(self, args):
        while(len(sys.argv) > 0):
            del sys.argv[0]
        if len(self.test.source_files) > 0:
            sys.argv.append(self.test.source_files[0])
        for arg in args:
            sys.argv.append(arg)
        reload_proboscis()

    def create_rst_from_source(self):
        """
        Copies the source files from a directory to .rst equiveaents in another
        directory.
        """
        make_dirs(self.rst_directory)
        for file_name in self.test.source_files:
            source_rel_path = join(self.test.base_directory, file_name)
            source_file = join(self.src_directory, source_rel_path)
            rst_file = join(self.rst_directory, file_name)
            create_rst("python", source_file, rst_file)

    def restore_modules(self):
        """Necessary to get the decorators to register tests again."""
        current_module_names = sys.modules.keys()
        delete_list = []
        for name in current_module_names:
            if name not in self.module_names:
                delete_list.append(name)
        for name in delete_list:
            del sys.modules[name]

    def run(self, run_info, index):
        """Manipulates various global variables before running a test.

        Of course it would be nicer to not use global variables and Proboscis
        even has facilities for this, but since the examples are written to use
        globals (for example most large test suites would use the default test
        registry via the @test decorator) its better to make the examples
        simpler at the expense of needing this code.

        Captures std out, changes the sys argv list to match the "args" field
        of the run information, then runs a test before asserting that the
        output was as expected. It mucks with proboscis's default registry (a global
        variable provided for convience that is used by the examples) and the
        Python module dictionry.
        """
        output_file_name = "output%d" % index
        self.alter_argv(run_info["args"])
        output_directory = join(self.base_directory, "output")
        output_file = join(output_directory, output_file_name + ".txt")
        make_dirs(output_directory)
        output = open(output_file, 'w')

        # Disable unittest's habit of murdering program on invocation.
        old_sys_exit = sys.exit
        sys.exit = fake_exit
        # Redirect standard out.
        old_std_out = sys.stdout
        sys.stdout = output

        # Pretend we're running this from a shell.
        #output.write("$ python run_tests.py " + str(run_info["args"]) + "\n\n")
        fake_sh_output = "$ python"
        for arg in sys.argv:
            fake_sh_output = fake_sh_output + " " + arg
        print(fake_sh_output + "\n\n")
        proboscis.case.OVERRIDE_DEFAULT_STREAM = output
        # Run the actual test, raise error if necessary.
        try:
            proboscis.decorators.DEFAULT_REGISTRY.reset()
            self.store_modules()
            self.test.run(index)
        finally:
            output.close()
            sys.stdout = old_std_out
            sys.exit = old_sys_exit

            failures = run_info["failures"]
            if sys.version_info < (2, 7) and not proboscis.dependencies.use_nose:
                failures += run_info["skips"]
            assert_failures_in_file(output_file, failures)
            rst_file = join(output_directory, output_file_name + ".rst")
            create_rst("bash", output_file, rst_file)

            self.restore_modules()

    def store_modules(self):
        self.module_names = list(sys.modules.keys())


class UnitTestExample(object):

    base_directory="unit"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":[]
        },
        {
            "args":["--group=strings"],
            "failures":[],
            "skips":[]
        },
        {
            "args":["--show-plan"],
            "failures":[],
            "skips":[]
        },
        {
            "args":["--verbosity=4"],
            "failures":[],
            "skips":[]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "unit.py")]

    def run(self, index):
        from tests.examples import unit
        sys.path.append(unit.__path__[0])
        from tests.examples.unit import run_tests as unit_run
        reload(unit_run)  # Reload to force a new Proboscis
        unit_run.run_tests()


class Example1(object):

    base_directory="example1"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":["Delete the user."],
        },
        {
            "args":[],
            "failures":[
                "Creates a local database and starts up the web service."],
            "skips":[
            "proboscis.case.FunctionTest (create_user)",
            "proboscis.case.FunctionTest (user_cant_connect_with_wrong_password)",
            "Make sure the given client cannot perform admin actions..",
            "Make sure the given client cannot perform admin actions..",
            "Test changing a client's profile image.",
            "Delete the user.",
            ]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py"),
                    join("tests", "unit_test.py")]

    def run(self, index):
        from tests.examples import example1
        sys.path.append(example1.__path__[0])
        if (index == 1):
            # Change the code during this run to show what happens when the
            # code is busted. This is for an unhappy path example in the docs.
            import mymodule
            mymodule.start_web_server = mymodule.bad_start_web_server
        from tests.examples.example1 import run_tests as example1_run
        example1_run.run_tests()


class Example2(Example1):

    base_directory="example2"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":[]
        },
        {
            "args":[],
            "failures":[
                "Starts up the web service."],
            "skips":["proboscis.case.FunctionTest (create_user)",
            "proboscis.case.FunctionTest (user_cant_connect_with_wrong_password)",
            "Make sure the given client cannot perform admin actions..",
            "Make sure the given client cannot perform admin actions..",
            "Test changing a client's profile image.",
            "proboscis.case.FunctionTest (delete_user)"
            ]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py")]

    def run(self, index):
        from tests.examples import example2
        sys.path.append(example2.__path__[0])
        if (index == 1):
            import mymodule
            mymodule.start_web_server = mymodule.bad_start_web_server
        from tests.examples.example2 import run_tests as example2_run
        example2_run.run_tests()


class Example3(Example1):

    base_directory="example3"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":[]
        },
        {
            "args":[],
            "failures":[
                "Create a user."],
            "skips":["Test changing a client's profile image.",
                "proboscis.case.MethodTest (delete_user)",
                "Make sure the given client cannot perform admin actions..",
                "Make sure the given client cannot perform admin actions..",
                "proboscis.case.MethodTest (cant_login_with_wrong_password)",
                "proboscis.case.MethodTest (successful_login)"]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py")]

    def run(self, index):
        from tests.examples import example2
        sys.path.append(example2.__path__[0])
        if index == 1:
            def return_nadda(*args):
                return None
            import mymodule
            mymodule.UserServiceClient.create_user = return_nadda
        from tests.examples.example3 import run_tests as example3_run
        example3_run.run_tests()


class Example4(Example1):

    base_directory="example4"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":[]
        },
        {
            "args":[],
            "failures":[
                "Create a user.",
                "Create a user."],
            "skips":["Test changing a client's profile image.",
                "Test changing a client's profile image.",
                "proboscis.case.MethodTest (delete_user)",
                "proboscis.case.MethodTest (delete_user)",
                "Make sure the given client cannot perform admin actions..",
                "Make sure the given client cannot perform admin actions..",
                "Make sure the given client cannot perform admin actions..",
                "Make sure the given client cannot perform admin actions..",
                "proboscis.case.MethodTest (successful_login)",
                "proboscis.case.MethodTest (successful_login)"]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py")]

    def run(self, index):
        from tests.examples import example2
        sys.path.append(example2.__path__[0])
        if index == 1:
            def return_nadda(*args):
                return None
            import mymodule
            mymodule.UserServiceClient.create_user = return_nadda
        from tests.examples.example4 import run_tests as example4_run
        example4_run.run_tests()


class ExampleF(Example1):

    base_directory="example_factory"

    runs = [
        {
            "args":[],
            "failures":[],
            "skips":[]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py")]

    def run(self, index):
        from tests.examples import example_factory
        sys.path.append(example_factory.__path__[0])
        import spam_api
        from tests.examples.example_factory import run_tests as exampleF_run
        exampleF_run.run_tests()


def run_all(root="."):
    if not os.path.exists(join(root, "docs")) or \
       not os.path.exists(join(root, "proboscis", "decorators.py")):
        raise ValueError("Please invoke this from the root of proboscis's "
                         "source.")
    ExampleRunner(root, UnitTestExample())
    ExampleRunner(root, Example1())
    ExampleRunner(root, Example2())
    ExampleRunner(root, Example3())
    ExampleRunner(root, Example4())
    if CAN_USE_WITH:
        ExampleRunner(root, ExampleF())


if __name__ == '__main__':
    run_all()
