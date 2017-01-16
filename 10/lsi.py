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
import scipy.sparse.linalg
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
        >>> m = ii.tdMatrix.todense()
        >>> m.view('i8,i8,i8').sort(order=['f1'], axis=0)
        >>> m
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

        self.tdMatrix = A

    def preprocessLsi(self, k):
        """Do LSI preprocessing. Perform SVD, compute V_k, U_k and U_k * S_k.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> r1 = [1.0, 1.0, 0.0, 1.0, 0.0, 0.0]
        >>> r2 = [1.0, 0.0, 1.0, 1.0, 0.0, 0.0]
        >>> r3 = [1.0, 1.0, 1.0, 2.0, 1.0, 1.0]
        >>> r4 = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        >>> ii.tdMatrix = [r1, r2, r3, r4]
        >>> ii.preprocessLsi(2)
        >>> ii.Uk[0] = [float('%.3f' % v) for v in  ii.Uk[0]]
        >>> ii.Uk[1] = [float('%.3f' % v) for v in  ii.Uk[0]]
        >>> ii.Uk[2] = [float('%.3f' % v) for v in  ii.Uk[0]]
        >>> ii.Uk[3] = [float('%.3f' % v) for v in  ii.Uk[0]]
        >>> ii.Uk
        array([[-0.47 ,  0.367],
               [-0.47 ,  0.367],
               [-0.47 ,  0.367],
               [-0.47 ,  0.367]])
        >>> ii.Vk[0] = [float('%.3f' % v) for v in  ii.Vk[0]]
        >>> ii.Vk[1] = [float('%.3f' % v) for v in  ii.Vk[0]]
        >>> ii.Vk
        array([[-0.529, -0.225, -0.225,  0.027,  0.556,  0.556],
               [-0.529, -0.225, -0.225,  0.027,  0.556,  0.556]])
        >>> ii.UkSk[0] = [float('%.3f' % v) for v in  ii.UkSk[0]]
        >>> ii.UkSk[1] = [float('%.3f' % v) for v in  ii.UkSk[0]]
        >>> ii.UkSk[2] = [float('%.3f' % v) for v in  ii.UkSk[0]]
        >>> ii.UkSk[3] = [float('%.3f' % v) for v in  ii.UkSk[0]]
        >>> ii.UkSk
        array([[-0.726,  1.397],
               [-0.726,  1.397],
               [-0.726,  1.397],
               [-0.726,  1.397]])
        """

        U, S, Vt = scipy.sparse.linalg.svds(self.tdMatrix, k)
        self.Uk = U[:, :k]
        self.Vk = Vt[:k, :]
        self.UkSk = self.Uk * S

    def processQueryLsi(self, q):
        r""" Execute the query by projecting the query vector to latent space.

        >>> import io
        >>> txt ='internet web surfing\ninternet surfing\nweb surfing\nintern'
        >>> txt +='et web surfing surfing beach\nsurfing beach\nsurfing beach'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> ii.preprocessVsm(4)
        >>> ii.preprocessLsi(2)
        >>> res = ii.processQueryLsi("web surfing")
        >>> [(x[0], 0.0) if x[1] == -0.0 else x for x in res]
        [(0, 0.944), (3, 0.705), (2, 0.568), (1, 0.568), (5, 0.0), (4, 0.0)]
        """

        Q = self.prepareQueryMatrix(q)
        qConc = Q * self.UkSk
        scores = qConc.dot(self.Vk)
        scores = numpy.round(scores, 3)
        scores = scores.tolist()[0]
        result = []
        for i in range(0, len(scores)):
            result.append((i, scores[i]))
        return sorted(result, key=lambda x: (float(x[1]), x[0]), reverse=True)

    def processQueryLsiComb(self, q, l):
        r""" Execute the query by projecting the query vector to latent space
        + linear combination with original scores.
        """

        Q = self.prepareQueryMatrix(q)
        qConc = Q * self.UkSk
        scores = l * Q * self.tdMatrix + (1 - l) * qConc.T * self.Vk
        scores = scores.tolist()[0]
        result = []
        for i in range(0, len(scores)):
            result.append((i, scores[i]))
        return sorted(result, key=lambda x: (float(x[1]), x[0]), reverse=True)

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

    def prepareQueryMatrix(self, q):
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
        return Q

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

        Q = self.prepareQueryMatrix(q)
        scores = Q.dot(self.tdMatrix)
        scores = scores.todense().tolist()[0]
        result = []
        for i in range(0, len(scores)):
            result.append((i, scores[i]))
        return sorted(result, key=lambda x: -x[1])

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

    def merge(self, a, b):
        """ Returns the union of two (sorted!!) postings lists

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> a = [(2, 0), (5, 2), (7, 7), (8, 6)]
        >>> b = [(4, 1), (5, 3), (6, 3), (8, 3), (9, 8)]
        >>> ii.merge(a, b)
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

    def setStopwords(self, lisd):
        self.stopwords = lisd

    def relatedTermPairs(self, k):
        """ Compute the term-term association matrix T. Return the k term pairs
        with highest values, sorted by their values.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> ii.invertedLists = {}
        >>> ii.invertedLists["lirum"] = [(2, 0.1)]
        >>> ii.invertedLists["larum"] = [(8, 0.8)]
        >>> ii.invertedLists["spoon"] = [(1, 0.2), (3, 0.6), (4, 0.1)]
        >>> ii.invertedLists["handle"] = [(2, 0.4), (3, 0.1), (4, 0.8)]
        >>> ii.preprocessVsm(4)
        >>> ii.preprocessLsi(2)
        >>> r = ii.relatedTermPairs(1)[0]
        >>> 'handle' in r
        True
        >>> 'spoon' in r
        True
        >>> r[2]
        0.285
        """

        T = self.Uk.dot(self.Uk.T)
        numpy.fill_diagonal(T, 0)  # get rid of same term values
        T = numpy.tril(T)          # get rid of duplicate values
        termMap = {v: k for k, v in self.rowIds.items()}
        vals = [item for sublist in T.tolist() for item in sublist]
        vals = sorted(vals, reverse=True)
        termPairs = []
        for val in vals[0:k]:
            pos = numpy.where(T == val)
            t1 = termMap[pos[0][0]]
            t2 = termMap[pos[1][0]]
            termPairs.append((t1, t2, val))
        return termPairs


class EvaluateBenchmark:
    """ Class with functions for computing MP@3, MP@R and MAP. """

    def precisionAtK(self, resultIds, relevantIds, k):
        """ Given lists of calculated, actually relevant record IDs and k,
        calculate P@k.

        >>> eb = EvaluateBenchmark()
        >>> eb.precisionAtK([0, 1, 2, 5, 6], [0, 2, 5, 6, 7, 8], 4)
        0.75
        """

        res = resultIds[0:k]
        hit = 0
        for r in relevantIds:
            if r in res:
                hit += 1
        return hit/k

    def precisionAtR(self, resultIds, relevantIds):
        """ Given lists of calculated and actually relevant record IDs,
        calculate P@R.

        >>> eb = EvaluateBenchmark()
        >>> eb.precisionAtR([0, 1, 2, 5], [0, 2, 5, 7, 11, 12])
        0.5
        """

        return self.precisionAtK(resultIds, relevantIds, len(relevantIds))

    def avgPrecision(self, resultIds, relevantIds):
        """ Given lists of calculated and actually relevant record IDs,
        calculate AP.

        >>> eb = EvaluateBenchmark()
        >>> eb.avgPrecision([582, 17, 5666, 10003, 10], [10, 582, 877, 10003])
        0.525
        """

        sum = 0.0
        matchedRelevant = 0
        for i, r in enumerate(resultIds):
            if r in relevantIds:
                matchedRelevant += 1
                sum += (matchedRelevant / (i + 1))
        return sum / len(relevantIds)

if __name__ == '__main__':
    """ Answer user queries for a file given as command line parameter. """

    if len(sys.argv) != 5:
        print('Usage: python3 inverted_index.py <recs> <k> <m> <benchmark>')
        sys.exit()

    recFileName = sys.argv[1]
    k = int(sys.argv[2])
    m = int(sys.argv[3])
    bmFileName = sys.argv[4]

    print('Building inverted index ...')
    with open(recFileName) as f:
        ii = InvertedIndex(f, 1.75, 0.3)
    print('done')

    stopwords = []
    with open('stopwords_en.txt') as f:
        for line in f:
            stopwords.append(line.strip())
    ii.setStopwords(stopwords)

    mode = input('\n[t]erm pairs or [b]enchmark?\n> ')
    if mode == 't':
        ii.preprocessVsm(m, l2normalize=_L2)
        ii.preprocessLsi(k)
        terms = ii.relatedTermPairs(100)
        with open('term_pairs.txt', 'w') as f:
            for t in terms:
                f.write('{0}, {1}   [{2}]\n'.format(t[0], t[1], t[2]))
    elif mode == 'b':
        eb = EvaluateBenchmark()
        with open(bmFileName) as f:
            mpAt3 = 0
            mpAtR = 0
            mAp = 0
            count = 0
            ii.preprocessVsm(m, l2normalize=_L2)
            ii.preprocessLsi(k)
            for line in f:
                query, idLine = line.strip().split('\t')
                relIds = idLine.split(' ')
                """ movies-benchmark.txt assumes movie IDs starting at 1
                whereas I work with IDs starting at 0, therefore I decrement
                all relevant IDs by 1. """
                relIds = [int(x)-1 for x in relIds]
                # result = ii.processQuery(query)
                # result = ii.processQueryVsm(query)
                # result = ii.processQueryLsi(query)
                result = ii.processQueryLsiComb(query, 0.67)
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
