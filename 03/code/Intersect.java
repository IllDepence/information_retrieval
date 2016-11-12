// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Patrick Brosi <brosi@informatik.uni-freiburg.de>,
//          Tarek Saier <tarek.saier@uranus.uni-freiburg.de>.

import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;

/**
 * Code for intersecting two posting lists.
 */
public class Intersect {

  /**
   * Read posting list from file.
   */
  PostingList readPostingListFromFile(String fileName) throws IOException {
    // First read docids and sores into two native arrays.
    FileReader fileReader = new FileReader(fileName);
    BufferedReader bufferedReader = new BufferedReader(fileReader);

    // get record count info
    String l = bufferedReader.readLine();
    int numRecords = Integer.parseInt(l);

    int[] ids = new int[numRecords + 1];
    int[] scores = new int[numRecords + 1];

    int i = 0;
    while (i < numRecords) {
      i++;
      String line = bufferedReader.readLine();
      if (line == null) {
        break;
      }
      String[] parts = line.split("\\W+");
      ids[i - 1] = Integer.parseInt(parts[0]);
      scores[i - 1] = Integer.parseInt(parts[1]);
    }
    // sentinels
    ids[numRecords] = Integer.MAX_VALUE;
    scores[numRecords] = 0;
    return new PostingList(ids, scores, i);
  }

  /**
   * Intersect two posting lists using an appropriate algorithm.
   */
  PostingList intersect(PostingList list1, PostingList list2) {
    PostingList small;
    PostingList large;
    if (list1.size < list2.size) {
      small = list1;
      large = list2;
    } else {
      small = list2;
      large = list1;
    }
    if (small.size * 100 < large.size) {
      return intersectBinary(small, large);
    } else {
      return intersectZipper(small, large);
    }
  }

  /**
   * Intersect two posting lists using binary search algorithm.
   */
  PostingList intersectBinary(PostingList small, PostingList large) {
    int[] ids = new int[small.size];
    int[] scores = new int[small.size];
    int size = 0;
    int lowerBound = 0;
    int[] result = new int[2];
    for (int i = 0; i < small.size; i++) {
      result = binarySearch(large, lowerBound, small.ids[i]);
      // not found
      if (result[0] == 0) {
        lowerBound = result[1];
      }
      // found
      if (result[0] == 1) {
        lowerBound = result[1];
        ids[size] = small.ids[i];
        scores[size] = (small.scores[i] + large.scores[result[1]]);
        size++;
      }
    }
    return new PostingList(ids, scores, size);
  }

  /**
   * Binary search for value in PostingList; return (success, id) tuple.
   */
  int[] binarySearch(PostingList large, int lowerBound, int search) {
    int dist = Integer.MAX_VALUE;
    int upperBound = large.size - 1;
    int suspect = Integer.MIN_VALUE;
    while (dist > 2) {
      suspect = ((upperBound - lowerBound) / 2) + lowerBound;
      if (large.ids[suspect] == search) {
        return new int[] {1, suspect};
      }
      if (large.ids[suspect] > search) {
        upperBound = suspect;
      } else {
        lowerBound = suspect;
      }
      dist = upperBound - lowerBound;
    }

    if (large.ids[lowerBound] == search) {
      return new int[] {1, lowerBound};
    }
    if (large.ids[upperBound] == search) {
      return new int[] {1, upperBound};
    }
    return new int[] {0, suspect};
  }

  /**
   * Intersect two posting lists using zipper algorithm.
   */
  PostingList intersectZipper(PostingList list1, PostingList list2) {
    int n1 = list1.ids.length;
    int n2 = list2.ids.length;
    int n = Math.min(n1, n2);  // max result size.
    int[] ids = new int[n];
    int[] scores = new int[n];
    int i = 0;
    int j = 0;
    int k = 0;
    while (true) {
      while (list1.ids[i] < list2.ids[j]) {
        i++;
      }
      while (list2.ids[j] < list1.ids[i]) {
        j++;
      }
      if (list1.ids[i] == list2.ids[j]) {
        if (list1.ids[i] == Integer.MAX_VALUE) {
          break;
        }
        ids[k] = list1.ids[i];
        scores[k] = (list1.scores[i] + list2.scores[j]);
        i++;
        j++;
        k++;
      }
    }

    return new PostingList(ids, scores, k);
  }
}
