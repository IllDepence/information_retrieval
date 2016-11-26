/**
  * As suggested in the forum.
  */
public class WordIdScorePedTriple {

  public WordIdScorePedTriple(int wordId, int score, int ped) {
    this.wordId = wordId;
    this.score = score;
    this.ped = ped;
  }

  @Override
  public String toString() {
    String w = Integer.toString(wordId);
    String s = Integer.toString(score);
    String p = Integer.toString(ped);
    return "(" + w + ", " + "p=" + p + ", s=" + s + ")";
  }

  public int wordId;
  public int score;
  public int ped;
}
