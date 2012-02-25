import org.testng.annotations.*;

@Test(groups= {"BeforeAndAfter"})
public class BeforeAndAfterWithNoMethods extends BeforeAndAfter {

    @BeforeClass
    public void beforeEverything() {
        println("@BeforeClass");
    }

    @BeforeMethod
    public void setUp() {
        println("@BeforeMethod");
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
