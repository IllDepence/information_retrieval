"""
Copyright 2016 Tarek Saier <tarek.saier@uranus.uni-freiburg.de>

This work is free. You can redistribute it and/or modify
it under the terms of the WTFPL, Version 2, as published
by Sam Hocevar. See the COPYING file for more details.
"""

import math
import re
import sys


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

    def merge(self, l1, l2):
        """ Merge two lists of recId bm25score touples by adding values.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO('foo'), 1.75, 0.75)
        >>> l1 = [(2, 0), (5, 2), (7, 7), (8, 6)]
        >>> l2 = [(4, 1), (5, 3), (6, 3), (8, 3), (9, 8)]
        >>> ii.merge(l1, l2)
        [(2, 0), (4, 1), (5, 5), (6, 3), (7, 7), (8, 9), (9, 8)]
        """

        i = 0
        j = 0
        result = []
        iDone = False
        jDone = False
        while not (iDone and jDone):
            if not iDone:
                t1 = l1[i]
            if not jDone:
                t2 = l2[j]

            if iDone:
                result.append(t2)
                j += 1
                if j == len(l2):
                    jDone = True
                continue
            if jDone:
                result.append(t1)
                i += 1
                if i == len(l1):
                    iDone = True
                continue

            if t1[0] == t2[0]:
                """ IDs match. Add scores, move both indices. """
                result.append((t1[0], t1[1]+t2[1]))
                i += 1
                j += 1
            elif t1[0] < t2[0]:
                """ Add list1's value before moving on. """
                result.append(t1)
                i += 1
            else:
                """ Add list2's value before moving on. """
                result.append(t2)
                j += 1

            if i == len(l1):
                iDone = True
            if j == len(l2):
                jDone = True

        return result

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
