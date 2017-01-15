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

_TF = False
_TFIDF = False
_L2 = False


class InvertedIndex:
    """ Class for creating an inverted index with BM25 scores based a text file
    w/ one entry per line. """

    def __init__(self, fileObj, bm25k, bm25b):
        r""" Create inverted index given a file object and BM25 parameters.

        >>> import io
        >>> import pprint
        >>> txt ='internet web surfing\ninternet surfing\nweb surfing\nintern'
        >>> txt +='et web surfing surfing beach\nsurfing beach\nsurfing beach'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> r = sorted(ii.invertedLists.items())
        >>> # Note: indices decremented by one because I start them at 0.
        >>> pprint.pprint(r[0])
        ('beach', [(3, 0.7054), (4, 1.1355), (5, 1.1355)])
        >>> pprint.pprint(r[1])
        ('internet', [(0, 0.9437), (1, 1.1355), (3, 0.7054)])
        >>> pprint.pprint(r[2][0])
        'surfing'
        >>> pprint.pprint(r[2][1])
        [(0, 0.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 0.0), (5, 0.0)]
        >>> pprint.pprint(r[3])
        ('web', [(0, 0.9437), (2, 1.1355), (3, 0.7054)])
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

        # -------- tf switch --------
        if _TF:
            return

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
                # -------- tf * idf switch --------
                if _TFIDF:
                    bm25score = tf * idf
                """ Precision to 4 decimals as in TIP file. """
                bm25score = float('{0:.4f}'.format(bm25score))
                tmpInvLists[word].append((recId, bm25score))

        self.invListSimpleTf = self.invertedLists  # save for doctest
        self.invertedLists = tmpInvLists

    def preprocessVsm(self, m, l2normalize=False):
        r""" Compute sparse term-document matrix using inverted index created
        in the class's constructor.

        >>> import io
        >>> txt ='internet web surfing\ninternet surfing\nweb surfing\nintern'
        >>> txt +='et web surfing surfing beach\nsurfing beach\nsurfing beach'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> ii.preprocessVsm(4)
        >>> ii.tdMatrix.view('i8,i8,i8').sort(order=['f1'], axis=0)
        >>> ii.tdMatrix
        matrix([[ 0.    ,  0.    ,  0.    ,  0.    ,  0.    ,  0.    ],
                [ 0.    ,  0.    ,  0.    ,  0.7054,  0.    ,  0.    ],
                [ 0.9437,  0.    ,  1.1355,  0.7054,  0.    ,  0.    ],
                [ 0.9437,  1.1355,  0.    ,  0.7054,  1.1355,  1.1355]])
        """

        # get sorted terms by df
        srtdTerms = sorted(self.invertedLists,
                           key=lambda x: len(self.invertedLists[x]),
                           reverse=True)
        # get m most frequent terms
        mfTerms = srtdTerms[0:m]

        nzVals = []
        rowInds = []
        colInds = []
        row = 0
        for fTerm in mfTerms:
            invList = self.invertedLists[fTerm]
            for recId, bm25score in invList:
                nzVals.append(bm25score)
                rowInds.append(row)
                colInds.append(recId)
            self.rowIds[fTerm] = row
            row += 1
        A = scipy.sparse.csr_matrix((nzVals, (rowInds, colInds)))

        if l2normalize:
            A = self.l2normalizeCols(A)

        self.tdMatrix = A.todense()

    def l2normalizeCols(self, matrix):
        """ Functions to L2-normalize the columns of the given matrix.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> m = scipy.sparse.csr_matrix([[ 0.7, 0.4, 0.1], [ 1.9, 0.5, 2.9]])
        >>> r = ii.l2normalizeCols(m).todense().tolist()
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

    def processQueryVsm(self, q):
        """ Process a query using the VSM. Return relevant documents sorted by
        their BM25-scores.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(0, 0.2), (2, 0.6)]
        >>> l2 = [(1, 0.4), (2, 0.1), (3, 0.8)]
        >>> ii.invertedLists = {"bla": l1, "blubb": l2}
        >>> ii.preprocessVsm(99)
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
        Q = scipy.sparse.csr_matrix((nzVals, (rowInds, colInds)),
                                    shape=(1, self.tdMatrix.shape[0]))
        scores = Q.dot(self.tdMatrix)
        scores = scores.tolist()[0]
        result = []
        for i in range(0, len(scores)):
            result.append((i, scores[i]))
        return sorted(result, key=lambda x: -x[1])

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
            ii.preprocessVsm(l2normalize=_L2)
            for line in f:
                query, idLine = line.strip().split('\t')
                relIds = idLine.split(' ')
                """ movies-benchmark.txt assumes movie IDs starting at 1
                whereas I work with IDs starting at 0, therefore I decrement
                all relevant IDs by 1. """
                relIds = [int(x)-1 for x in relIds]
                # result = ii.processQuery(query)
                result = ii.processQueryVsm(query)
                resIds = [r[0] for r in result]
                pAt3 = eb.precisionAtK(resIds, relIds, 3)
                pAtR = eb.precisionAtR(resIds, relIds)
                ap = eb.avgPrecision(resIds, relIds)
                # print('\nQuery: {0}'.format(query))
                # print('P@3 {0:.2f} | P@R {1:.2f} | AP: {2:.2f}'.format(
                #     pAt3, pAtR, ap))
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
