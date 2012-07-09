import org.testng.annotations.*;

@Test(groups= {"BeforeAndAfter"})
public class BeforeMethodFailure extends BeforeAndAfter  {

    @BeforeClass(alwaysRun=true)
    public void beforeEverything() {
        println("@BeforeClass");
        assert false;
    }

    @BeforeMethod
    public void setUp() {
        println("@BeforeMethod");
        assert false;
    }

    @Test(groups={"abc"})
    public void method1() {
        println("@Test 1");
    }

    @Test
    public void method2() {
        println("@Test 2");
    }

    @AfterClass(alwaysRun=true)
    public void afterEverything() {
        println("@AfterClass");
    }

    @AfterMethod
    public void tearDown() {
        println("@AfterMethod");
    }
}
