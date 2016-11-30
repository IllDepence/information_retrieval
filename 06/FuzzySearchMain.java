// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,

import java.io.IOException;
import java.util.ArrayList;

/**
 *
 */
public class FuzzySearchMain {

  public static void main(String[] args) throws IOException {
    // Parse command line arguments.
    if (args.length != 1) {
      System.out.println("Usage: FuzzySearchMain <entities file>");
      System.exit(1);
    }
    String fileName = args[0];

    System.out.print("Reading strings and building index...");

    // Build q-gram index.
    QGramIndex qgi = new QGramIndex(3);
    qgi.buildFromFile(fileName);

    System.out.println(" done.");

    // Read user input
    ArrayList<WordIdScorePedTriple> matches =
      new ArrayList<WordIdScorePedTriple>();
    while (true) {
      System.out.print("\nQuery: ");
      String input = System.console().readLine();
      long startTime = System.currentTimeMillis();
      input = input.toLowerCase().replaceAll("\\W", "");
      double num = (double) input.length();
      double den = 4.0;
      int delta = (int) Math.floor(num / den);
      matches = qgi.findMatches(input, delta);
      matches = qgi.sortRes(matches);
      long endTime = System.currentTimeMillis();
      Long duration = (endTime - startTime);

      System.out.println("##### Result #####");
      for (int i = 0; i < Math.min(5, matches.size()); i++) {
        System.out.println(qgi.getEnityById(matches.get(i).wordId));
      }
      if (matches.size() > 5) {
        System.out.println("(+" + Integer.toString(matches.size() - 5)
          + " more)");
      }
      System.out.println("Execution time: " + duration.toString() + "ms");
    }
  }
}
