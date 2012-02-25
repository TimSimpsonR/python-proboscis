from proboscis import *

class BeforeAndAfter(object):

    def getName(self):
        return str(type(self))

    def println(self, msg):
        print("%s : %s" % (self.getName(), msg))


class BeforeAndAfterSuccess(BeforeAndAfter):

    @before_class
    def beforeEverything(self):
        self.println("@BeforeClass");


    @before_method
    def setUp(self):
        self.println("@BeforeMethod")

    @test
    def method1(self):
        self.println("@Test 1")

    @test
    def method2(self):
        self.println("@Test 2")

    @after_class
    def afterEverything(self):
        self.println("@AfterClass")

    @after_method
    def tearDown(self):
        self.println("@AfterMethod")
