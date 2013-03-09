from proboscis import test
from proboscis import TestProgram

order = []

def mark(msg):
    global order
    order += msg

@test(groups="A")
class ClassA(object):

    @test
    def methodA1(self):
        mark("A1")

    @test
    def methodA2(self):
        mark("A2")


@test(groups="B")
class ClassB(object):

    @test(depends_on=[ClassA])
    def methodB1(self):
        mark("B1")

    @test
    def methodB2(self):
        mark("B2")



if __name__ == '__main__':    TestProgram().run_and_exit()
