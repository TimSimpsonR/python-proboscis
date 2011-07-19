from proboscis import TestProgram

def run_tests():
    from tests import unit
    # Run Proboscis and exit.
    TestProgram().run_and_exit()

if __name__ == '__main__':
    print("GO")
    run_tests()
