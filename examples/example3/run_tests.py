from proboscis import register
from proboscis import TestProgram

def run_tests():
    from tests import service_tests

    # Now create some groups of groups.
    register(groups=["integration"],
             depends_on_groups=["service.initialize",
                                "service.tests",
                                "service.shutdown"])
    register(groups=["slow"],
             depends_on_groups=["fast", "integration"])

    # Run Proboscis and exit.
    TestProgram().run_and_exit()
    

if __name__ == '__main__':
    run_tests()
