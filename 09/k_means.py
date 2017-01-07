"""
Copyright 2016 Tarek Saier <tarek.saier@uranus.uni-freiburg.de>

This work is free. You can redistribute it and/or modify
it under the terms of the WTFPL, Version 2, as published
by Sam Hocevar. See the COPYING file for more details.
"""

import math
import numpy
import re
import scipy.sparse
import sys


class KMeans:
    """ Class for k-means clustering, with vectors built from an inverted
    index. """

    def __init__(self, fileObj, bm25k, bm25b):
        r""" Create inverted index given a file object and BM25 parameters.

        >>> import io
        >>> import pprint
        >>> txt ='first docum.\nsecond second docum.\nthird third third docum.'
        >>> f = io.StringIO(txt)
        >>> km = KMeans(f, 1.75, 0.75)
        >>> pprint.pprint(sorted(km.invListSimpleTf.items()))
        [('docum', [(0, 1), (1, 1), (2, 1)]),
         ('first', [(0, 1)]),
         ('second', [(1, 2)]),
         ('third', [(2, 3)])]
        >>> pprint.pprint(sorted(km.invertedLists.items()))
        [('docum', [(0, 0.0), (1, 0.0), (2, 0.0)]),
         ('first', [(0, 1.8848)]),
         ('second', [(1, 2.3246)]),
         ('third', [(2, 2.5207)])]
        """

        self.k = bm25k
        self.b = bm25b
        self.invertedLists = {}
        self.records = {}
        self.avdl = 0
        recordId = 0

        self.tdMatrix = None
        self.rowIds = {}

        """ Pass 1: calculate tf, dl and avdl. """
        for line in fileObj:
            if recordId not in self.records:
                self.records[recordId] = {}
            self.records[recordId]['line'] = line
            self.records[recordId]['dl'] = 0
            for word in re.split('\W+', line):
                if len(word) > 0:
                    word = word.lower()
                    self.records[recordId]['dl'] += 1
                    self.avdl += 1

                    """ First occurence of word in file, create inv. list. """
                    if word not in self.invertedLists:
                        self.invertedLists[word] = []

                    """ First occurence of word in record, add tuple w/ 0. """
                    if len(self.invertedLists[word]) == 0 or\
                       self.invertedLists[word][-1][0] != recordId:
                        self.invertedLists[word].append((recordId, 0))
                    """ Increase tf by 1 from 0 or previous value. """
                    currTf = self.invertedLists[word][-1][1]
                    self.invertedLists[word][-1] = (recordId, currTf + 1)

            recordId += 1

        self.numDocs = recordId  # started at 0, increased at loop end
        self.avdl = self.avdl / self.numDocs

        """ Pass 2: calculate tf*idf and bm25. """
        tmpInvLists = {}
        for word, invList in self.invertedLists.items():
            df = len(invList)
            tmpInvLists[word] = []
            for recId, tf in invList:
                dl = self.records[recId]['dl']
                numer = tf * (self.k+1)
                denom = self.k * (1-self.b + ((self.b*dl) / self.avdl)) + tf
                bm25tf = numer / denom
                idf = math.log2(self.numDocs / df)
                bm25score = bm25tf * idf
                # FIXME: save tf*idf for later here
                """ Precision to 4 decimals as in TIP file. """
                bm25score = float('{0:.4f}'.format(bm25score))
                tmpInvLists[word].append((recId, bm25score))

        self.invListSimpleTf = self.invertedLists  # save for doctest
        self.invertedLists = tmpInvLists

    def preprocessVsm(self, l2normalize=True):
        """ Compute sparse term-document matrix using inverted index created in
        the class's constructor.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (2, 0.6)] # ids decremented because my sheet 2 code
        >>>                           # counts record ids beginning at 0.
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> km.invertedLists = {"bla": l1, "blubb": l2}
        >>> km.preprocessVsm(l2normalize=False)
        >>> r = km.tdMatrix.todense().tolist()
        >>> print(sorted(r))
        [[0.0, 0.4, 0.1, 0.8], [0.2, 0.0, 0.6, 0.0]]
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (1, 0.2), (2, 0.6)]
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> km.invertedLists = {"blibb": l1, "blabb": l2}
        >>> km.preprocessVsm(l2normalize=True)
        >>> r = km.tdMatrix.todense().tolist()
        >>> r[0] = [float('%.3f' % v) for v in r[0]]
        >>> r[1] = [float('%.3f' % v) for v in r[1]]
        >>> print(sorted(r))
        [[0.0, 0.894, 0.164, 1.0], [1.0, 0.447, 0.986, 0.0]]
        """

        nzVals = []
        rowInds = []
        colInds = []
        row = 0
        for word, invList in self.invertedLists.items():
            for recId, bm25score in invList:
                nzVals.append(bm25score)
                rowInds.append(row)
                colInds.append(recId)
            self.rowIds[word] = row
            row += 1
        A = scipy.sparse.csr_matrix((nzVals, (rowInds, colInds)))

        if l2normalize:
            A = self.l2normalizeCols(A)

        self.tdMatrix = A

    def l2normalizeCols(self, matrix):
        """ Functions to L2-normalize the columns of the given matrix.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> m = scipy.sparse.csr_matrix([[ 0.7, 0.4, 0.1], [ 1.9, 0.5, 2.9]])
        >>> r = km.l2normalizeCols(m).todense().tolist()
        >>> r[0] = [float('%.3f' % v) for v in r[0]]
        >>> r[1] = [float('%.3f' % v) for v in r[1]]
        >>> r[0]
        [0.346, 0.625, 0.034]
        >>> r[1]
        [0.938, 0.781, 0.999]
        """

        # square values
        squared = matrix.multiply(matrix)
        # sum squares and take squareroot
        a = numpy.sqrt(squared.sum(0))
        # divide each column by the the L^2 norm
        return matrix.multiply(scipy.sparse.csr_matrix(1/a))

    def kMeans(self, k):
        """ Cluster into k clusters using k-means and return k final centroids.
        """

        pass

    def initializeCentroids(self, k):
        """ Compute an m x k matrix with the initial (random) centroids.
        """

        pass

    def computeDistances(self, documents, centroids):
        """ Compute a k x n matrix such that the entry at i, j contains the
        distance between the i-th centroid and the j-th document.
        """

        # A: term-doc matrix (one doc per col)
        # C: term-centroid matrix (one centroid per col)
        # transpose(C) * A yields matrix were entry at i, j is dot product
        #     between centroid i and document j

        pass

    def computeAssignment(self, distances):
        """ Assign each document to its closest centroid.
        """

        pass

    def computeCentroids(self, docs, assignment):
        """ Compute an m x k matrix with new, normalized centroids.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> docs = numpy.matrix([[1, 0, 1], [0, 1, 0]])
        >>> assignment = numpy.matrix([[0, 1, 0], [0, 0, 1], [1, 0, 0]])
        >>> res = km.computeCentroids(docs, assignment)
        >>> res.todense().tolist()
        [[0.0, 1.0, 1.0], [1.0, 0.0, 0.0]]
        """

        res = scipy.sparse.csr_matrix(docs * assignment.transpose())
        return self.l2normalizeCols(res)


if __name__ == '__main__':
    """ Compute clusters and print output based on command line parameters. """

    if len(sys.argv) != 3:
        print('Usage: python3 k_means.py <filename> <k>')
        sys.exit()

    print('Building inverted index ...')
    fileName = sys.argv[1]
    with open(fileName) as f:
        km = KMeans(f, 1.2, 0.5)
    print('done')

    # 1. Arguments: <records> <k>
    # 2. Construct inverted index from given file
    # 3. Build normalized term-document matrix
    # 4. Run k-means with given k
    # 5. Print the top-10 terms of each cluster.
