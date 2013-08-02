from proboscis import register
from proboscis import TestProgram

import unittest
from proboscis.decorators import DEFAULT_REGISTRY
from proboscis.case import TestPlan
from proboscis.case import TestSuiteCreator


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
    from proboscis.subunit import SubUnitInitiator
    SubUnitInitiator().run_and_exit()


def testsuite():
    from tests import service_tests

    # Now create some groups of groups.
    register(groups=["fast"], depends_on_groups=["unit"])
    register(groups=["integration"],
             depends_on_groups=["service.initialize",
                                "service.tests",
                                "service.shutdown"])
    register(groups=["slow"],
             depends_on_groups=["fast", "integration"])


    # plan = TestPlan.create_from_registry(DEFAULT_REGISTRY)
    # suite = plan.create_test_suite(unittest.TestLoader(), unittest.TestSuite())
    # return suite
    from proboscis.subunit import create_testr_parallel_suite
    plan = TestPlan.create_from_registry(DEFAULT_REGISTRY)
    suite = create_testr_parallel_suite(plan)
    return suite


if __name__ == '__main__':
    run_tests()
    #print(testsuite())

