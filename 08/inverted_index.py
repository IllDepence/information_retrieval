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
from operator import itemgetter


class InvertedIndex:
    """ Class for creating an inverted index with BM25 scores based a text file
    w/ one entry per line. """

    def __init__(self, fileObj, bm25k, bm25b):
        r""" Create inverted index given a file object and BM25 parameters.

        >>> import io
        >>> import pprint
        >>> txt ='first docum.\nsecond second docum.\nthird third third docum.'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> pprint.pprint(sorted(ii.invListSimpleTf.items()))
        [('docum', [(0, 1), (1, 1), (2, 1)]),
         ('first', [(0, 1)]),
         ('second', [(1, 2)]),
         ('third', [(2, 3)])]
        >>> pprint.pprint(sorted(ii.invertedLists.items()))
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
        self.stopwords = []

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

        """ Pass 2: calculate tf* idf. """
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
                """ Precision to 4 decimals as in TIP file. """
                bm25score = float('{0:.4f}'.format(bm25score))
                tmpInvLists[word].append((recId, bm25score))

        self.invListSimpleTf = self.invertedLists  # save for doctest
        self.invertedLists = tmpInvLists

    def preprocessVsm(self, l2normalize=False):
        """ Compute sparse term-document matrix using inverted index created in
        the class's constructor.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (2, 0.6)] # ids decremented because my sheet 2 code
        >>>                           # counts record ids beginning at 0.
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> ii.invertedLists = {"bla": l1, "blubb": l2}
        >>> ii.preprocessVsm()
        >>> r = ii.tdMatrix.todense().tolist()
        >>> print(sorted(r))
        [[0.0, 0.4, 0.1, 0.8], [0.2, 0.0, 0.6, 0.0]]
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (1, 0.2), (2, 0.6)]
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> ii.invertedLists = {"blibb": l1, "blabb": l2}
        >>> ii.preprocessVsm(l2normalize=True)
        >>> r = ii.tdMatrix.todense().tolist()
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
        self.tdMatrix = A

        if l2normalize:
            B = scipy.sparse.lil_matrix(A)
            for i in range(0, B.get_shape()[1]):
                col = B[:,i]
                div = numpy.linalg.norm(col.todense())
                col = col.multiply(1/div)
                B[:,i] = col
            self.tdMatrix = scipy.sparse.csr_matrix(B)

    def merge(self, a, b):
        """
        Returns the union of two (sorted!!) postings lists

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(2, 0), (5, 2), (7, 7), (8, 6)]
        >>> l2 = [(4, 1), (5, 3), (6, 3), (8, 3), (9, 8)]
        >>> ii.merge(l1, l2)
        [(2, 0), (4, 1), (5, 5), (6, 3), (7, 7), (8, 9), (9, 8)]
        """

        res = []
        i = 0
        j = 0
        while i < len(a) and j < len(b):
            if a[i][0] < b[j][0]:
                res.append(a[i])
                i += 1
            elif b[j][0] < a[i][0]:
                res.append(b[j])
                j += 1
            else:
                res.append((a[i][0], a[i][1] + b[j][1]))
                i += 1
                j += 1
        while i < len(a):
            res.append(a[i])
            i += 1
        while j < len(b):
            res.append(b[j])
            j += 1
        return res

    def processQueryVsm(self, q):
        """ Process a query using the VSM. Return relevant documents sorted by
        their BM25-scores.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (2, 0.6)]
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> ii.invertedLists = {"bla": l1, "blubb": l2}
        >>> ii.preprocessVsm()
        >>> ii.processQueryVsm("bla blubb") # as above, rec/doc ids from 0
        [(3, 0.8), (2, 0.7), (1, 0.4), (0, 0.2)]
        >>> ii.processQueryVsm("bla blubb bla blubb")
        [(3, 1.6), (2, 1.4), (1, 0.8), (0, 0.4)]
        """

        keywords = q.split(' ')
        keywords = [w.lower() for w in keywords]
        keywords = [w for w in keywords if w not in self.stopwords]

        weighted = {}
        for k in keywords:
            if k not in weighted:
                weighted[k] = 0
            weighted[k] += 1
        nzVals = []
        rowInds = []
        colInds = []
        for key, val in weighted.items():
            if key not in self.rowIds:
                continue
            nzVals.append(val)
            rowInds.append(0)
            colInds.append(self.rowIds[key])
        Q = scipy.sparse.csr_matrix((nzVals, (rowInds, colInds)))
        scores = Q.dot(self.tdMatrix)
        scores = scores.todense().tolist()[0]
        result = []
        for i in range(0, len(scores)):
            result.append((i, scores[i]))
        return sorted(result, key=lambda x:-x[1])

    def processQuery(self, q):
        r""" Given a list of keywords, find the 3 best maches accoding to
        BM25.

        >>> import io
        >>> import pprint
        >>> txt ='first docum.\nsecond second docum.\nthird third third docum.'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> ii.processQuery('docum third')
        [(2, 2.5207), (0, 0.0), (1, 0.0)]
        """

        keywords = q.split(' ')
        keywords = [w.lower() for w in keywords]
        keywords = [w for w in keywords if w not in self.stopwords]

        """ Special cases. """
        if len(keywords) == 0:
            return []
        if len(keywords) == 1:
            if keywords[0] not in self.invertedLists:
                return []
            rawList = self.invertedLists[keywords[0]]
            sortdList = sorted(rawList, key=lambda x: -x[1])
            return sortdList

        """ Actual merging. """
        list1 = self.invertedLists[keywords[0]]
        for i in range(1, len(keywords)):
            if keywords[i] in self.invertedLists:
                list2 = self.invertedLists[keywords[i]]
                list1 = self.merge(list1, list2)

        sortdList = sorted(list1, key=lambda x: -x[1])
        return sortdList

    def setStopwords(self, lisd):
        self.stopwords = lisd


class EvaluateBenchmark:
    """ Class with functions for computing MP@3, MP@R and MAP. """

    def precisionAtK(self, resultsIds, relevantIds, k):
        """ Given lists of calculated, actually relevant record IDs and k,
        calculate P@k.

        >>> eb = EvaluateBenchmark()
        >>> eb.precisionAtK([0, 1, 2, 5, 6], [0, 2, 5, 6, 7, 8], 4)
        0.75
        """

        res = resultsIds[0:k]
        hit = 0
        for r in relevantIds:
            if r in res:
                hit += 1
        return hit/k

    def precisionAtR(self, resultsIds, relevantIds):
        """ Given lists of calculated and actually relevant record IDs,
        calculate P@R.

        >>> eb = EvaluateBenchmark()
        >>> eb.precisionAtR([0, 1, 2, 5], [0, 2, 5, 7, 11, 12])
        0.5
        """

        return self.precisionAtK(resultsIds, relevantIds, len(relevantIds))

    def avgPrecision(self, resultsIds, relevantIds):
        """ Given lists of calculated and actually relevant record IDs,
        calculate AP.

        >>> eb = EvaluateBenchmark()
        >>> eb.avgPrecision([582, 17, 5666, 10003, 10], [10, 582, 877, 10003])
        0.525
        """

        pSum = 0
        for relId in relevantIds:
            if relId not in resultsIds:
                continue
            else:
                k = resultsIds.index(relId) + 1
                pSum += self.precisionAtK(resultsIds, relevantIds, k)

        return pSum/len(relevantIds)

if __name__ == '__main__':
    """ Answer user queries for a file given as command line parameter. """

    if len(sys.argv) != 2:
        print('Usage: python3 inverted_index.py <filename>')
        sys.exit()

    print('Building inverted index ...')
    fileName = sys.argv[1]
    with open(fileName) as f:
        ii = InvertedIndex(f, 1.2, 0.5)
    print('done')

    stopwords = []
    with open('stopwords_en.txt') as f:
        for line in f:
            stopwords.append(line.strip())
    ii.setStopwords(stopwords)

    mode = input('\n[i]nteractive or [b]enchmark?\n> ')
    if mode == 'i':
        while True:
            queryLine = input('\nEnter a query (space separated keywords)\n> ')
            matches = ii.processQuery(queryLine)
            for recId, score in matches[0:3]:
                text = ii.records[recId]['line'].strip()
                for keyword in queryLine.split(' '):
                    patt = r'\b(' + keyword + r')\b'
                    text = re.sub(patt, '[32m\g<0>[0m', text, flags=re.I)
                print('[1m[{0:.4f}][0m: {1}'.format(score, text))
    elif mode == 'b':
        eb = EvaluateBenchmark()
        with open('movies-benchmark.txt') as f:
            mpAt3 = 0
            mpAtR = 0
            mAp = 0
            count = 0
            for line in f:
                query, idLine = line.strip().split('\t')
                relIds = idLine.split(' ')
                """ movies-benchmark.txt assumes movie IDs starting at 1
                whereas I work with IDs starting at 0, therefore I decrement
                all relevant IDs by 1. """
                relIds = [int(x)-1 for x in relIds]
                result = ii.processQuery(query)
                resIds = [r[0] for r in result]
                pAt3 = eb.precisionAtK(resIds, relIds, 3)
                pAtR = eb.precisionAtR(resIds, relIds)
                ap = eb.avgPrecision(resIds, relIds)
                print('\nQuery: {0}'.format(query))
                print('P@3 {0:.2f} | P@R {1:.2f} | AP: {2:.2f}'.format(
                    pAt3, pAtR, ap))
                mpAt3 += pAt3
                mpAtR += pAtR
                mAp += ap
                count += 1
            mpAt3 = mpAt3 / count
            mpAtR = mpAtR / count
            mAp = mAp / count
            print('\nAverage:')
            print('MP@3 {0:.2f} | MP@R {1:.2f} | MAP: {2:.2f}'.format(
                mpAt3, mpAtR, mAp))
    else:
        sys.exit()
