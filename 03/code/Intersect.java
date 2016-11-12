// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Patrick Brosi <brosi@informatik.uni-freiburg.de>.

import java.util.ArrayList;
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
    // First read into two ArrayList objects docids and sores.
    FileReader fileReader = new FileReader(fileName);
    BufferedReader bufferedReader = new BufferedReader(fileReader);

    // get record count info
    String l = bufferedReader.readLine();
    int numRecords = Integer.parseInt(l);

    ArrayList<Integer> ids = new ArrayList<Integer>(numRecords);
    ArrayList<Integer> scores = new ArrayList<Integer>(numRecords);

    int i = 0;
    while (i < numRecords) {
      i++;
      String line = bufferedReader.readLine();
      if (line == null) {
        break;
      }
      String[] parts = line.split("\\W+"); 
      ids.add(Integer.parseInt(parts[0]));
      scores.add(Integer.parseInt(parts[1]));
    }
    return new PostingList(ids, scores);
  }

  /**
   * Intersect two posting lists using the simple "zipper" algorithm.
   */
  PostingList intersect(PostingList list1, PostingList list2) {
    int n1 = list1.ids.length;
    int n2 = list2.ids.length;
    int n = Math.min(n1, n2);  // max result size.
    ArrayList<Integer> ids = new ArrayList<Integer>(n);
    ArrayList<Integer> scores = new ArrayList<Integer>(n);
    int i = 0;
    int j = 0;
    while (i < n1 && j < n2) {
      while (i < n1 && list1.ids[i] < list2.ids[j]) {
        i++;
      }
      
      if (i == n1) {
        break;
      }

      while (j < n2 && list2.ids[j] < list1.ids[i]) {
        j++;
      }

      if (j == n2) {
        break;
      }
      
      if (list1.ids[i] == list2.ids[j]) {
        ids.add(list1.ids[i]);
        scores.add(list1.scores[i] + list2.scores[j]);
        i++;
        j++;
      }
    }
    return new PostingList(ids, scores);
  }
}
