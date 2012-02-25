import org.testng.annotations.*;

@Test(groups= {"BeforeAndAfter"})
public class BeforeMethodFailure2 extends BeforeAndAfter  {

    public static int count = 0;

    @BeforeClass
    public void beforeEverything() {
        println("@BeforeClass");
    }

    @BeforeMethod
    public void setUp() {
        println("@BeforeMethod");
        count ++;
        assert count < 2;
    }

    @Test
    public void method1() {
        println("@Test 1");
    }

    @Test
    public void method2() {
        println("@Test 2");
    }

    @AfterClass
    public void afterEverything() {
        println("@AfterClass");
    }

    @AfterMethod
    public void tearDown() {
        println("@AfterMethod");
    }
}
