from proboscis import register
from proboscis.case import UnittestTestInitator

def run_tests():
    from tests import service_tests

    # Now create some groups of groups.
    register(groups=["fast"], depends_on_groups=["unit"])
    register(groups=["integration"],
             depends_on_groups=["service.initialize",
                                "service.tests",
                                "service.shutdown"])
    register(groups=["slow"],
             depends_on_groups=["fast", "integration"])

    # Run Proboscis and exit.
    UnittestTestInitator().run_and_exit()


if __name__ == '__main__':
    run_tests()
