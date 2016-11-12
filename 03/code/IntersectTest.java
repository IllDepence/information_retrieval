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
    list1.clean();
    Assert.assertEquals("[10, 20, 30]", Arrays.toString(list1.ids));
    Assert.assertEquals("[1, 2, 3]", Arrays.toString(list1.scores));
    PostingList list2 = i.readPostingListFromFile("example2.txt");
    list2.clean();
    Assert.assertEquals("[10, 20, 40]", Arrays.toString(list2.ids));
    Assert.assertEquals("[1, 2, 4]", Arrays.toString(list2.scores));
  }

  @Test
  public void intersect() throws IOException {
    Intersect i = new Intersect();
    PostingList list1 = new PostingList();
    PostingList list2 = new PostingList();

    list1.ids = new int[] {5, 10, 20, 30, 50, 60, Integer.MAX_VALUE};
    list1.scores = new int[] {0, 1, 2, 3, 4, 5, 0};
    list1.size = 6;
    list2.ids = new int[] {1, 2, 3, 10, 20, 40, 61, Integer.MAX_VALUE};
    list2.scores = new int[] {1, 5, 4, 1, 2, 4, 9, 0};
    list2.size = 7;

    PostingList result = i.intersect(list1, list2);
    result.clean();

    Assert.assertEquals("[10, 20]", Arrays.toString(result.ids));
    Assert.assertEquals("[2, 4]", Arrays.toString(result.scores));
  }

  @Test
  /**
   * Case where one list is more than 100 times larger, which triggers binary
   * algorithm.
   */
  public void intersectBinary() throws IOException {
    Intersect i = new Intersect();
    PostingList list1 = new PostingList();
    PostingList list2 = new PostingList();

    list1.ids = new int[] {34, Integer.MAX_VALUE};
    list1.scores = new int[] {7, 0};
    list1.size = 1;
    list2.ids = new int[102];
    list2.scores = new int[102];
    for (int j = 0; j < 101; j++) {
      list2.ids[j] = j;
      list2.scores[j] = j * 2;
    }
    list2.ids[101] = Integer.MAX_VALUE;
    list2.scores[101] = 0;
    list2.size = 101;

    PostingList result = i.intersect(list1, list2);
    result.clean();

    Assert.assertEquals("[34]", Arrays.toString(result.ids));
    // 7 + (34 * 2)
    Assert.assertEquals("[75]", Arrays.toString(result.scores));
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
