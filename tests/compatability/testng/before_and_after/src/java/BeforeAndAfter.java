import org.testng.annotations.*;

@Test(groups= {"BeforeAndAfter"})
public class BeforeAndAfter {

    protected String getName() {
        return this.getClass().toString();
    }

    protected void println(String msg) {
        System.out.println(getName() + " : " + msg);
    }

}
