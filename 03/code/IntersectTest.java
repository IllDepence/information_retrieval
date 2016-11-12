// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Patrick Brosi <brosi@informatik.uni-freiburg.de>.

import java.util.Arrays;
import org.junit.Test;
import org.junit.Assert;
import java.io.IOException;

/**
 * One unit test for each non-trivial method in the Intersect class.
 */
public class IntersectTest {

  @Test
  public void readPostingListFromFile() throws IOException {
    Intersect i = new Intersect();
    PostingList list1 = i.readPostingListFromFile("example1.txt");
    Assert.assertEquals("[10, 20, 30]", Arrays.toString(list1.ids));
    Assert.assertEquals("[1, 2, 3]", Arrays.toString(list1.scores));
    PostingList list2 = i.readPostingListFromFile("example2.txt");
    Assert.assertEquals("[10, 20, 40]", Arrays.toString(list2.ids));
    Assert.assertEquals("[1, 2, 4]", Arrays.toString(list2.scores));
  }

  @Test
  public void intersect() throws IOException {
    Intersect i = new Intersect();
    PostingList list1 = new PostingList();
    PostingList list2 = new PostingList();

    list1.ids = new int[] {5, 10, 20, 30, 50, 60};
    list1.scores = new int[] {0, 1, 2, 3, 4, 5};
    list2.ids = new int[] {1, 2, 3, 10, 20, 40, 61};
    list2.scores = new int[] {1, 5, 4, 1, 2, 4, 9};

    PostingList result = i.intersect(list1, list2);
    result.clean();

    Assert.assertEquals("[10, 20]", Arrays.toString(result.ids));
    Assert.assertEquals("[2, 4]", Arrays.toString(result.scores));
  }

  /**
   * +++ IMPORTANT +++
   *
   * You have to implement tests for each new method you add to the Intersect
   * class.
   *
   * In particular, your improved "intersect" method should run the 'intersect'
   * test above successfully.
   *
   * If you add several intersection methods with different strategies,
   * EACH of them must also be tested seperately! See the example below.
   *
   **/

  /*
    @Test
  public void myShinyNewIntersect() throws IOException {
    Intersect i = new Intersect();
    PostingList list1 = new PostingList();
    PostingList list2 = new PostingList();

    list1.ids = new int[] {5, 10, 20, 30, 50, 60};
    list1.scores = new int[] {0, 1, 2, 3, 4, 5};
    list2.ids = new int[] {1, 2, 3, 10, 20, 40, 61};
    list2.scores = new int[] {1, 5, 4, 1, 2, 4, 9};

    PostingList result = i.myShinyNewIntersect(list1, list2);
    Assert.assertEquals("[10, 20]", Arrays.toString(result.ids));
    Assert.assertEquals("[2, 4]", Arrays.toString(result.scores));
  }
  */
}
