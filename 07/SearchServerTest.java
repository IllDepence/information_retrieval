import org.junit.Test;
import org.junit.Assert;
import java.io.UnsupportedEncodingException;

/**
 * One unit test for each non-trivial method in the QGramIndex class.
 */
public class SearchServerTest {

  @Test
  public void urlDecode() throws UnsupportedEncodingException {
    Assert.assertEquals("zürich", SearchServerMain.urlDecode("z%C3%BCrich"));
    Assert.assertEquals("Løkken", SearchServerMain.urlDecode("L%C3%B8kken"));
    Assert.assertEquals("a o", SearchServerMain.urlDecode("a+o"));
    Assert.assertEquals("á é", SearchServerMain.urlDecode("%C3%A1+%C3%A9"));
    Assert.assertEquals("á é", SearchServerMain.urlDecode("%C3%A1%20%C3%A9"));
  }

  @Test
  public void jsonStringEscape() throws UnsupportedEncodingException {
    Assert.assertEquals("Hello\\\\Goodbye!", SearchServerMain.jsonStringEscape(
      "Hello\\Goodbye!"));
    Assert.assertEquals("\\\"Hello\\\"", SearchServerMain.jsonStringEscape(
      "\"Hello\""));
  }

}
