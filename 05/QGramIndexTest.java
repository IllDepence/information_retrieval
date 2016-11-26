// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,

import org.junit.Test;
import org.junit.Assert;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;

/**
 * One unit test for each non-trivial method in the QGramIndex class.
 */
public class QGramIndexTest {

  @Test
  public void buildFromFile() throws IOException {
    QGramIndex qgi = new QGramIndex(3);
    qgi.buildFromFile("example.txt");
    Assert.assertEquals(16, qgi.invertedLists.size());
    Assert.assertEquals(4, qgi.invertedLists.get("$fo").size());
    Assert.assertEquals(3, qgi.invertedLists.get("oot").size());
    Assert.assertEquals(2, qgi.invertedLists.get("tba").size());
  }

  @Test
  public void getQGrams() {
    QGramIndex qgi = new QGramIndex(3);
    Assert.assertEquals("[$$l, $li, lir, iru, rum]",
        qgi.getQGrams("lirum").toString());
  }

  @Test
  public void computeUnion() {
    QGramIndex qgi = new QGramIndex(3);
    ArrayList<ArrayList<Integer>> lists = new ArrayList<ArrayList<Integer>>();
    lists.add(new ArrayList<Integer>(Arrays.asList(1, 4, 6)));
    lists.add(new ArrayList<Integer>(Arrays.asList(2, 4, 6, 9, 9)));
    Assert.assertEquals("[1, 2, 4, 4, 6, 6, 9, 9]",
        qgi.computeUnion(lists).toString());
  }

  @Test
  public void checkPrefixEditDistance() {
    QGramIndex qgi = new QGramIndex(3);
    Assert.assertEquals(0, qgi.checkPrefixEditDistance("foo", "foo", 0));
    Assert.assertEquals(0, qgi.checkPrefixEditDistance("foo", "foo", 10));
    Assert.assertEquals(0, qgi.checkPrefixEditDistance("foo", "foot", 0));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("foot", "foo", 1));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("foo", "fotbal", 1));
    Assert.assertEquals(3, qgi.checkPrefixEditDistance("foo", "bar", 3));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("perf", "perv", 1));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("perv", "perf", 1));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("perf", "peff", 1));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("foot", "foo", 0));
    Assert.assertEquals(1, qgi.checkPrefixEditDistance("foo", "fotbal", 0));
    Assert.assertEquals(3, qgi.checkPrefixEditDistance("foo", "bar", 2));
  }

  @Test
  public void findMatches() throws IOException {
    QGramIndex qgi = new QGramIndex(3);
    qgi.buildFromFile("example.txt");
    Assert.assertEquals("[(0, p=0, s=3), (1, p=1, s=1), "
        + "(2, p=0, s=2), (3, p=0, s=1)]",
        qgi.findMatches("foot", 1).toString());
    Assert.assertEquals("[(1, p=1, s=1)]",
        qgi.findMatches("woob", 1).toString());
  }
}
