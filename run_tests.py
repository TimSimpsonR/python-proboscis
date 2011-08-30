import os
import sys

from abc import ABCMeta
from nose.tools import assert_equal
from os.path import join

import proboscis


def fake_exit(*args, **kwargs):
    pass

def make_dirs(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

class FailureLines(object):
    """Tallies expected and actual occurrences of lines in output."""

    def __init__(self, lines):
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
                "Expected to see failure for \"%s\" %d time(s) but saw it "
                "%d time(s).  Additional info for this test: %s" %
                (line, info["expected"], info["actual"], str(self.failures)))

    def get(self, line):
        if line not in self.failures:
            self.failures[line] = {"expected":0, "actual":0}
        return self.failures[line]


def assert_failures_in_file(source_file, expected_failures):
    """Checks the output of Proboscis run for expected failures."""
    failures = FailureLines(expected_failures)
    # This isn't solid at all but works fine in the limited use cases.
    for line in open(source_file, 'r'):
        if "FAIL: " in line:
            failures.add_actual(line[6:].strip())
        elif "ERROR: " in line:
            failures.add_actual(line[7:].strip())
    failures.assert_all()


def create_rst(block_type, source_file, rst_file):
    """Converts Python files into a .rst files in the docs/build directory."""
    print(source_file + " ---> " + rst_file)
    if not os.path.exists(source_file):
        raise ValueError("File %s not found." % source_file)
    make_dirs(os.path.dirname(rst_file))
    with open(rst_file, 'w') as output:
        def code_block():
            output.write(".. code-block:: " + block_type + "\n\n")
        code_block()
        for line in open(source_file, 'r'):
            if line.strip() == "#rst-break":
                code_block()
            else:
                output.write("    " + line)

class ExampleRunner(object):

    def __init__(self, root, test):
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
        reload(proboscis)

    def create_rst_from_source(self):
        make_dirs(self.rst_directory)
        for file_name in self.test.source_files:
            source_rel_path = join(self.test.base_directory, file_name)
            source_file = join(self.src_directory, source_rel_path)
            rst_file = join(self.rst_directory, file_name)
            create_rst("python", source_file, rst_file)

    def restore_modules(self):
        """Necessary to get the decorators to register tests again."""
        current_module_names = sys.modules.keys()
        for name in current_module_names:
            if name not in self.module_names:
                del sys.modules[name]

    def run(self, run_info, index):
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
        proboscis.OVERRIDE_DEFAULT_STREAM = output
        # Run the actual test, raise error if necessary.
        try:
            proboscis.DEFAULT_REGISTRY.reset()
            self.store_modules()
            self.test.run(index)
        finally:
            output.close()
            sys.stdout = old_std_out
            sys.exit = old_sys_exit

            assert_failures_in_file(output_file, run_info["failures"])
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
            "failures":[]
        },
        {
            "args":["--group=strings"],
            "failures":[]
        },
        {
            "args":["--show-plan"],
            "failures":[]
        },
        {
            "args":["--verbosity=4"],
            "failures":[]
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
            "failures":[]
        },
        {
            "args":[],
            "failures":[
                "Start up web server then issue a connect to make sure its up."]
        }
    ]

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py"),
                    join("tests", "unit_test.py")]

    def run(self, index):
        from tests.examples import example1
        sys.path.append(example1.__path__[0])
        if (index == 1):
            import mymodule
            mymodule.start_web_server = mymodule.bad_start_web_server
        from tests.examples.example1 import run_tests as example1_run
        example1_run.run_tests()


class Example2(Example1):

    base_directory="example2"

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



def run_all(root="."):
    if not os.path.exists(join(root, "docs")) or \
       not os.path.exists(join(root, "proboscis", "decorators.py")):
        raise ValueError("Please invoke this from the root of proboscis's "
                         "source.")
    ExampleRunner(root, UnitTestExample())
    ExampleRunner(root, Example1())
    ExampleRunner(root, Example2())

if __name__ == '__main__':
    run_all()
