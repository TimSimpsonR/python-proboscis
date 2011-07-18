import os
import sys

from abc import ABCMeta
from os.path import join

import proboscis


def fake_exit(*args, **kwargs):
    pass

def make_dirs(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

def py2rst(py_file, rst_file):
    """Converts Python files into a .rst files in the docs/build directory."""
    if not os.path.exists(py_file):
        raise ValueError("File %s not found." % py_file)
    make_dirs(os.path.dirname(rst_file))
    with open(rst_file, 'w') as output:
        output.write(".. code-block:: python\n\n")
        output.writelines(("    " + line for line in open(py_file, 'r')))


def run_test(root, test):
    """Runs an example as if it was executing in that directory

    Records the output in an output file and stores the example code as RST
    files.

    """
    # Disable unittest's habit of murdering program on invocation.
    old_sys_exit = sys.exit
    sys.exit = fake_exit

    # Turn source files into rst files for docs
    base_directory = join(root, "docs", "build", "examples",
                          test.base_directory)
    rst_directory = join(base_directory, "source")
    src_directory = join(root, "tests", "examples")

    make_dirs(rst_directory)
    for source_file in test.source_files:
        py_file = join(src_directory, test.base_directory, source_file)
        rst_file = join(rst_directory, source_file)
        py2rst(py_file, rst_file)

    output_directory = join(base_directory, "output")
    make_dirs(output_directory)
    with open(join(output_directory, "output.txt"), 'w') as output:
        # Redirect standard out.
        old_std_out = sys.stdout
        sys.stdout = output

        # Pretend we're running this from a shell.
        output.write("$ python run_tests.py\n\n")
        proboscis._override_default_stream = output
        # Run the actual test, raise error if necessary.
        try:
            test.run()
        finally:
            sys.stdout = old_std_out
            # Give it back its weapons.
            sys.exit = old_sys_exit


class Example1(object):

    base_directory="example1"

    source_files = ["run_tests.py",
                    join("tests", "service_tests.py"),
                    join("tests", "unit_test.py")]

    def run(self):
        from tests.examples import example1
        sys.path.append(example1.__path__[0])
        from tests.examples.example1 import run_tests
        run_tests.run_tests()


def run_all(root="."):
    if not os.path.exists(join(root, "docs")) or \
       not os.path.exists(join(root, "proboscis", "decorators.py")):
        raise ValueError("Please invoke this from the root of proboscis's "
                         "source.")
    run_test(root, Example1())

if __name__ == '__main__':
    run_all()
