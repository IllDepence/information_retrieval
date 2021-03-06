"""
Copyright 2016 Tarek Saier <tarek.saier@uranus.uni-freiburg.de>

This work is free. You can redistribute it and/or modify
it under the terms of the WTFPL, Version 2, as published
by Sam Hocevar. See the COPYING file for more details.
"""

import math
import numpy
import random
import re
import scipy.sparse
import sys
import time


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
        self.idfs = {}
        self.words = {}
        recordId = 0

        self.tdMatrix = None

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
                self.idfs[word] = idf
                bm25score = bm25tf * idf
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
            self.words[row] = word
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
        >>> [float('%.3f' % v) for v in r[0]]
        [0.346, 0.625, 0.034]
        >>> [float('%.3f' % v) for v in r[1]]
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

        prevCentroids = self.initializeCentroids(k)
        prevRSS = sys.maxsize
        iterations = 0
        while True:
            distances = self.computeDistances(self.tdMatrix, prevCentroids)
            assignment = self.computeAssignment(distances)
            centroids = self.computeCentroids(self.tdMatrix, assignment)
            RSS = self.calcRSS(distances)
            iterations += 1
            if (prevRSS - RSS < 10):
                break
            if (centroids - prevCentroids).nnz == 0:
                break
            prevCentroids = centroids
            prevRSS = RSS
        print('Clustering iterations: {0}'.format(iterations))
        print('Final RSS: {0}'.format(int(RSS)))

        return centroids

    def calcRSS(self, distances):
        """ Calculate RSS

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> r1 = [6, 8, 6]
        >>> r2 = [8, 6, 8]
        >>> r3 = [9, 9, 9]
        >>> dists = scipy.sparse.csr_matrix([r1, r2, r3])
        >>> km.calcRSS(dists)
        18
        """

        return numpy.sum(numpy.nanmin(distances.todense(), axis=0))

    def initializeCentroids(self, k):
        """ Compute an m x k matrix with the initial (random) centroids.

        Doctest:
        Initializing is done by just using random documents (i.e. random
        colums form the term document matrix) as centroids. To test this we use
        a matrix with columns of same numbers, request a slice and test for
        equality.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> r1 = [1, 2, 3, 4, 5, 6, 7]
        >>> r2 = [1, 2, 3, 4, 5, 6, 7]
        >>> km.tdMatrix = scipy.sparse.csr_matrix([r1, r2])
        >>> res = km.initializeCentroids(1)
        >>> res.todense().tolist()[0] == res.todense().tolist()[1]
        True
        """

        m, n = self.tdMatrix.get_shape()
        colIdxs = []

        for i in range(k):
            colIdxs.append(int(random.random() * n))
        mtrx = self.tdMatrix[:, colIdxs]
        return scipy.sparse.csr_matrix(mtrx)

    def computeDistances(self, docs, centroids):
        """ Compute a k x n matrix such that the entry at i, j contains
        (distance between the i-th centroid and the j-th document)^2 * 1/2.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> r1 = [0.9806, 0.0995, 0.9991]
        >>> r2 = [0.1961, 0.9950, 0.0425]
        >>> docs = scipy.sparse.csr_matrix([r1, r2])
        >>> centroids = numpy.matrix([[0.5812, 0.6000], [0.8137, 0.8000]])
        >>> res = km.computeDistances(docs, centroids)
        >>> r = res.todense().tolist()
        >>> [float('%.3f' % v) for v in r[0]]
        [0.736, 0.515, 0.877]
        >>> [float('%.3f' % v) for v in r[1]]
        [0.714, 0.537, 0.856]
        """

        prod = scipy.sparse.csr_matrix(centroids.transpose() * docs)
        ones = numpy.ones(prod.get_shape())
        diff = scipy.sparse.csr_matrix(ones - prod)
        return diff.multiply(2).sqrt()

    def computeAssignment(self, distances):
        """ Assign each document to its closest centroid.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> r1 = [0.600, 0.800, 0.600]
        >>> r2 = [0.800, 0.600, 0.800]
        >>> dists = scipy.sparse.csr_matrix([r1, r2])
        >>> r = km.computeAssignment(dists)
        >>> r.todense().tolist()
        [[1, 0, 1], [0, 1, 0]]
        """

        numClusters, numDocs = distances.get_shape()
        nzVals = [1]*numDocs
        colInds = [i for i in range(numDocs)]
        rowInds = numpy.argmin(distances.todense(), axis=0).tolist()[0]
        return scipy.sparse.csr_matrix((nzVals, (rowInds, colInds)))

    def computeCentroids(self, docs, assignment):
        """ Compute an m x k matrix with new, normalized centroids.

        >>> import io
        >>> km = KMeans(io.StringIO('foo'), 1.75, 0.75)
        >>> docs = scipy.sparse.csr_matrix([[1, 0, 1], [0, 1, 0]])
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

    fileName = sys.argv[1]
    k = int(sys.argv[2])

    print('Building inverted index ...')
    with open(fileName) as f:
        km = KMeans(f, 1.2, 0.5)
    print('done')

    start = time.time()
    km.preprocessVsm()
    end = time.time()
    timeBuildMatrix = float('%.1f' % (end-start))
    print('Build time: {0}s'.format(timeBuildMatrix))

    start = time.time()
    centroids = km.kMeans(k)
    end = time.time()
    timeClustering = int(end-start)
    print('Clustering time: {0}s'.format(timeClustering))

    for i in range(k):
        print('Cluster #{0}'.format(i+1))
        clusterCol = centroids[:, i].todense().tolist()
        clusterVals = {}
        for j in range(len(clusterCol)):
            x = clusterCol[j][0]
            idf = km.idfs[km.words[j]]
            clusterVals[km.words[j]] = x * idf
        s = [(k, clusterVals[k]) for k in sorted(clusterVals,
                                                 key=clusterVals.get,
                                                 reverse=True)]
        for word, val in s[0:10]:
            print('    - {0} ({1:.2f})'.format(word, val))
