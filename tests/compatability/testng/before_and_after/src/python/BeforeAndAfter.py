from proboscis import *

class BeforeAndAfter(object):

    def getName(self):
        return str(type(self))

    def bad(self):
        print("FAILURE! This should not print!")

@test
class BeforeAndAfterSuccess(BeforeAndAfter):

    @before_class
    def beforeEverything(self):
        pass


    # @before_method
    # def setUp(self):
    #     self.println("@BeforeMethod")

    @test
    def method1(self):
        pass

    @test
    def method2(self):
        pass

    @after_class
    def afterEverything(self):
        pass

    # @after_method
    # def tearDown(self):
    #     self.println("@AfterMethod")

@test(groups= ["BeforeAndAfter"])
class BeforeClassFailure(BeforeAndAfter):

    @before_class
    def beforeEverything(self):
        assert false

    @test
    def method1(self):
        self.bad()

    @test
    def method2(self):
        self.bad()


    @after_class
    def afterEverything(self):
        self.bad()
