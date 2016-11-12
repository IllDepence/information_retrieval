// Copyright 2015, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Hannah Bast <bast@cs.uni-freiburg.de>.

import java.util.ArrayList;

/**
 * A posting list, with pairs doc id, score (both ints).
 */
public class PostingList {

  public PostingList() { }

  public PostingList(ArrayList<Integer> ids, ArrayList<Integer> scores) {
    int n = ids.size();
    this.ids = new int[n];
    this.scores = new int[n];
    for (int i = 0; i < n; i++) {
      this.ids[i] = ids.get(i);
      this.scores[i] = scores.get(i);
    }
  }

  public int ids[];
  public int scores[];
}
