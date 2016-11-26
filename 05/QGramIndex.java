// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,
//          Tarek Saier

import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.util.Collections;
import java.util.TreeMap;
import java.util.ArrayList;

/**
 * First steps towards a q-gram index, written during class.
 */
public class QGramIndex {

  /**
   * Create an empty QGramIndex.
   */
  public QGramIndex(int q) {
    this.invertedLists = new TreeMap<String, ArrayList<Integer>>();
    this.scoreList = new TreeMap<Integer, Integer>();
    this.entites = new ArrayList<String>();
    this.q = q;
    this.padding = new String(new char[q - 1]).replace("\u0000", "$");
  }

  /**
   * Build index from given list of entites (one line per entity, columns are:
   * entity name, score, ...).
   */
  public void buildFromFile(String fileName) throws IOException {
    FileReader fileReader = new FileReader(fileName);
    BufferedReader bufferedReader = new BufferedReader(fileReader);
    String line;
    int entityId = 0;
    while ((line = bufferedReader.readLine()) != null) {
      String name = line.split("\t")[0];
      int score = Integer.parseInt(line.split("\t")[1]);
      for (String qGram : getQGrams(name)) {
        if (!invertedLists.containsKey(qGram)) {
          invertedLists.put(qGram, new ArrayList<Integer>());
        }
        invertedLists.get(qGram).add(entityId);
      }
      scoreList.put(entityId, score);
      entites.add(name);
      entityId += 1;
    }
  }

  /**
   * Compute q-grams for padded, normalized version of given string.
   */
  public ArrayList<String> getQGrams(String name) {
    name = padding + name.toLowerCase().replaceAll("\\W", "");
    ArrayList<String> result = new ArrayList<String>();
    for (int i = 0; i < name.length() - q + 1; i++) {
      result.add(name.substring(i, i + q));
    }
    return result;
  };

  /**
   * Compute the union of the given inverted lists from the q-gram index.
   */
  public ArrayList<Integer> computeUnion(ArrayList<ArrayList<Integer>> lists) {
    ArrayList<Integer> result = new ArrayList<Integer>();
    for (int i = 0; i < lists.size(); i++) {
      result.addAll(lists.get(i));
    }
    Collections.sort(result);
    return result;
  }

  /**
   * Compute the prefix edit distance from the given query to the given string.
   */
  int checkPrefixEditDistance(String prefix, String string, int delta) {
    prefix = "#" + prefix;
    string = "#" + string;
    int maxcolumns = prefix.length() + delta; // + 1 due to the # added
    int numcols = Math.min(string.length(), maxcolumns);

    int[][] matrix = new int[prefix.length()][numcols];

    // fill first column v
    for (int i = 0; i < prefix.length(); i++) {
      matrix[i][0] = i;
    }
    // fill remainder of first row >
    for (int j = 1; j < numcols; j++) {
      matrix[0][j] = j;
    }

    // fill out rest of the matrix
    int min = Integer.MAX_VALUE;
    for (int i = 1; i < prefix.length(); i++) {
      for (int j = 1; j < numcols; j++) {
        int top = matrix[i - 1][j];
        int left = matrix[i][j - 1];
        int diag = matrix[i - 1][j - 1];
        int add = 1;
        int val = Math.min(diag, Math.min(top, left)) + add;
        if (prefix.substring(i, i + 1).equals(string.substring(j, j + 1))) {
          if (diag < val) {
            val = diag;
          }
        }
        matrix[i][j] = val;
        if (i + 1 == prefix.length()) { // last row
          min = Math.min(min, val);
        }
      }
    }

    /*
    for (int i = 0; i < prefix.length(); i++) {
      String line = "";
      for (int j = 0; j < numcols; j++) {
        line = line + Integer.toString(matrix[i][j]);
      }
      System.out.println(line);
    }
    */

    return Math.min(min, delta + 1);
  }

  /**
   * For the given query prefix, find all word IDs to which the prefix edit
   * distance is at most the given delta..
   */
  ArrayList<WordIdScorePedTriple> findMatches(String prefix, int delta) {
    ArrayList<String> queryQGrams = getQGrams(prefix);
    ArrayList<ArrayList<Integer>> preLst = new ArrayList<ArrayList<Integer>>();

    for (int i = 0; i < queryQGrams.size(); i++) {
      if (invertedLists.containsKey(queryQGrams.get(i))) {
        preLst.add(invertedLists.get(queryQGrams.get(i)));
      }
    }
    ArrayList<Integer> union = computeUnion(preLst);

    // get candidates
    TreeMap<Integer, Integer> numCommons = new TreeMap<Integer, Integer>();
    ArrayList<Integer> candidates = new ArrayList<Integer>();
    for (int i = 0; i < union.size(); i++) {
      if (!numCommons.containsKey(union.get(i))) {
        numCommons.put(union.get(i), 0);
      }
      int newVal = numCommons.get(union.get(i)) + 1;
      numCommons.put(union.get(i), newVal);
      if (newVal >= delta && !candidates.contains(union.get(i))) {
        candidates.add(union.get(i));
      }
    }

    // check PED for candidates
    ArrayList<WordIdScorePedTriple> result =
      new ArrayList<WordIdScorePedTriple>();
    for (int i = 0; i < candidates.size(); i++) {
      int id = candidates.get(i);
      String entity = entites.get(id).toLowerCase().replaceAll("\\W", "");
      int ped = checkPrefixEditDistance(prefix, entity, delta);
      if (ped <= delta) {
        result.add(new WordIdScorePedTriple(id, scoreList.get(id), ped));
      }
    }

    return result;
  }

  // The value of q.
  protected int q;

  // The padding (q - 1 times $).
  protected String padding;

  // The inverted lists.
  protected TreeMap<String, ArrayList<Integer>> invertedLists;

  // Map for storing scores.
  protected TreeMap<Integer, Integer> scoreList;

  // Array for entries
  protected ArrayList<String> entites;

};
