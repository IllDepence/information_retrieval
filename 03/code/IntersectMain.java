// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Patrick Brosi <brosi@informatik.uni-freiburg.de>..

import java.io.IOException;

/**
 * 
 */
public class IntersectMain {

  public static void main(String[] listNames) throws IOException {
    if (listNames.length < 2) {
      System.out.println("Usage IntersectMain.jar <posting lists>");
      System.exit(1);
    }

    // Read lists.
    int m = listNames.length;
    PostingList lists[] = new PostingList[m];
    Intersect is = new Intersect();
    System.out.println();
    for (int i = 0; i < listNames.length; i++) {
      System.out.print("Reading list \"" + listNames[i] + "\" ... ");
      System.out.flush();
      lists[i] = is.readPostingListFromFile(listNames[i]);
      System.out.println("done, size = " +  lists[i].ids.length);
    }

    // Intersect all pairs.
    System.out.println();
    int totalRuns = 0;
    int totalTime = 0;

    for (int i = 0; i < m; i++) {
      for (int j = 0; j < i; j++) {
        totalRuns++;
        System.out.print(
            "Intersecting " + listNames[i] + " + " + listNames[j] + " ... ");
        System.out.flush();
        long time1 = System.nanoTime();
        PostingList result = is.intersect(lists[i], lists[j]);
        long time2 = System.nanoTime();
        long time = (time2 - time1) / 1000;
        totalTime += time;

        System.out.println("result size = " + result.ids.length + ", "
            + "time = " + time + "µs");
      }
    }
    System.out.println();

    int averageTime = totalTime / totalRuns;
    System.out.format("Average time = %d µs%n", averageTime);
    System.out.println();
  }
}
