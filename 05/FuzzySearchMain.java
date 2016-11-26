// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Authors: Hannah Bast <bast@cs.uni-freiburg.de>,

import java.io.IOException;

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

    System.out.print(" done.\n");
  }
}
