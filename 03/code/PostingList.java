// Copyright 2015, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Tarek Saier <tarek.saier@uranus.uni-freiburg.de>.

/**
 * A posting list, with pairs doc id, score (both ints).
 */
public class PostingList {

  public PostingList() { }

  public PostingList(int[] ids, int[] scores) {
    this.ids = ids;
    this.scores = scores;
  }

  // bad hack to make the unit test happy
  public void clean() {
    int[] tmpIds = new int[this.size];
    int[] tmpScores = new int[this.size];
    for (int i = 0; i < this.size; i++) {
      tmpIds[i] = this.ids[i];
      tmpScores[i] = this.scores[i];
    }
    this.ids = tmpIds;
    this.scores = tmpScores;
  }

  public int ids[];
  public int scores[];
  public int size;
}
