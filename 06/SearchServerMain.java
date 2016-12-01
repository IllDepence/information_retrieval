// Copyright 2016, University of Freiburg,
// Chair of Algorithms and Data Structures.
// Author: Hannah Bast <bast@cs.uni-freiburg.de>.

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.DataOutputStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.io.FileInputStream;
import java.io.File;
import java.util.ArrayList;
import java.net.URLDecoder;

/**
 * Demo search server.
 */
public class SearchServerMain {

  public static void main(String[] args) throws IOException {

    // Parse the command line arguments.
    if (args.length < 2) {
      System.out.println("Usage: java -jar SearchServerMain.jar <file> <port>");
      System.exit(1);
    }
    String inputFile = args[0];
    int port = Integer.parseInt(args[1]);

    ServerSocket server = new ServerSocket(port);
    BufferedWriter out = null;

    // Set up fuzzy search
    System.out.print("Reading strings and building index...");
    QGramIndex qgi = new QGramIndex(3);
    qgi.buildFromFile(inputFile);
    System.out.println(" done.");
    ArrayList<WordIdScorePedTriple> matches =
      new ArrayList<WordIdScorePedTriple>();

    while (true) {
      String responseStatus = "";
      String responseType = "text/plain";
      String contentString = "";
      StringBuilder response = new StringBuilder();

      System.out.print("Waiting for query on port " + port +  " ... ");
      Socket client = server.accept();

      BufferedReader requestReader = new BufferedReader(
          new InputStreamReader(client.getInputStream()));
      String requestString = requestReader.readLine();
      System.out.println("Request string is " + requestString);

      // Handle requests
      if (requestString.startsWith("GET /")) {
        if (requestString.startsWith("GET / HTTP/")) {
          requestString = "GET /index.html";
        }
        // For the moment we don't care about request headers
        String requestURL = requestString.substring(5).split(" HTTP/")[0];

        // Decompose request URL
        String[] reqParts = requestURL.split("\\?");
        String requestPath = reqParts[0];
        String requestQuery = "";
        if (reqParts.length > 1) {
          requestQuery = reqParts[1];
        }
        if (requestQuery.matches("q=.*")) {
          // AJAX request
          String query = requestQuery.split("=")[1]; //assuming no use of &
          query = URLDecoder.decode(query, "UTF-8");
          String queryOrg = query;
          query = query.toLowerCase().replaceAll("\\W", "");
          double num = (double) query.length();
          double den = 4.0;
          int delta = (int) Math.floor(num / den);
          matches = qgi.findMatches(query, delta);
          matches = qgi.sortRes(matches);

          // building JSON by hand because why not ...
          // (this will so break if queryOrg includes unescaped JSON syntax)
          StringBuilder json = new StringBuilder();
          json.append("{\"query\": \"" + queryOrg + "\",\"results\":[");
          for (int i = 0; i < Math.min(30, matches.size()); i++) {
            String city = qgi.getEnityById(matches.get(i).wordId);
            String score = Integer.toString(matches.get(i).score);
            String ped = Integer.toString(matches.get(i).ped);
            if (i != 0) {
              json.append(",");
            }
            json.append("{\"city\": \"" + city + "\","
              + "\"score\": " + score + ","
              + "\"ped\": " + ped + "}");
          }
          json.append("]}");

          responseStatus = "200 OK";
          responseType = "application/json";
          contentString = json.toString();
        } else if (requestPath.matches("^[A-Za-z0-9_\\.-]+$")) {
          // Nice request for a file in our local directory
          File file = new File(requestPath);
          if (file.canRead()) {
            responseStatus = "200 OK";
          } else {
            responseStatus = "404 Not Found";
            requestPath = "404.html";
            file = new File(requestPath);
          }
          // Handle content types
          if (requestPath.matches(".*\\.html$")) {
            responseType = "text/html";
          } else if (requestPath.matches(".*\\.js$")) {
            responseType = "application/javascript";
          } else if (requestPath.matches(".*\\.css$")) {
            responseType = "text/css";
          }
          FileInputStream fis = new FileInputStream(file);
          byte[] bytes = new byte[(int) file.length()];
          fis.read(bytes);
          contentString = new String(bytes, "UTF-8");
        } else {
          // Naughty request with a path or other ominous content we don't want
          responseStatus = "418 I'm a teapot";
          contentString = "Nothing to exploit here. I'm just teapot. Go away."
            + "\r\n\r\nOr, if you're so inclined, help me find my buddy "
            + "\"Russell's\". I can't seem to find him.\r\n";
        }
      } else {
        responseStatus = "405 Method Not Allowed";
        contentString = "We're only doing GET requests, sorry.\n";
      }

      response.append("HTTP/1.1 " + responseStatus + "\r\n");
      response.append("Content-Length:  "
        + Integer.toString(contentString.getBytes("UTF-8").length) + "\r\n");
      response.append("Content-Type: " + responseType + "\r\n");
      response.append("\r\n");
      response.append(contentString);

      DataOutputStream responseWriter = new DataOutputStream(
        client.getOutputStream());
      responseWriter.write(response.toString().getBytes("UTF-8"));
      responseWriter.flush();
      responseWriter.close();
      requestReader.close();
      client.close();
    }
  }
}
