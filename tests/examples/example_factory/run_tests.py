from proboscis import register
from proboscis import TestProgram

def run_tests():
    from tests import service_tests
    # Run Proboscis and exit.
    TestProgram().run_and_exit()


if __name__ == '__main__':
    run_tests()
