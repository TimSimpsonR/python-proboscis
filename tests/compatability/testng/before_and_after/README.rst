Explores how the "before and after" annotations from TestNG work.

Test methods inside of a class with a @BeforeClass or @BeforeMethod annotation
have a relationship similar to dependsOn, in that if the annotated methods fail
then the other methods are skipped.

@AfterClass and @AfterMethod run after all methods in a class, and after each
method respectively. However, the relationship is different than dependsOn in
that if the method fails the @AfterMethod and @AfterClass methods will still
run. However, @AfterMethod and @AfterClass methods both have a dependsOn
relationship with @BeforeClass and even @BeforeMethod, in that if one of those
fail both the methods and the "after" methods will not run.

Additionally if @BeforeMethod runs successfully the first time then
@AfterMethod will run, but if the same @BeforeMethod runs again and fails @AfterMethod will not run though @AfterClass still will run. @AfterClass then
seems to only run if a test method executes.

In the absense of test methods none of these decorators run at all.





