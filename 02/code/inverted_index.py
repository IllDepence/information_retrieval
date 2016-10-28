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

        """ Pass 1: calculate tf, dl and avdl. """
        for line in fileObj:
            if recordId not in self.records:
                self.records[recordId] = {}
            self.records[recordId]['line'] = line
            self.records[recordId]['dl'] = 0
            for word in re.split('\W+', line):
                if len(word) > 0:
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
        r""" Merge two lists of recId bm25score touples by adding values.

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
        while i < len(l1) and j < len(l2):
            t1 = l1[i]
            t2 = l2[j]

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
        """ Append rest of longer list. """
        if len(l1) > len(l2):
            for k in range(len(l2), len(l1)):
                result.append(l1[k])
        elif len(l2) > len(l1):
            for k in range(len(l1), len(l2)):
                result.append(l2[k])

        return result

    def process_query(self, q):
        r""" Given a list of keywords, find the 3 best maches accoding to
        BM25.

        >>> import io
        >>> import pprint
        >>> txt ='first docum.\nsecond second docum.\nthird third third docum.'
        >>> f = io.StringIO(txt)
        >>> ii = InvertedIndex(f, 1.75, 0.75)
        >>> ii.process_query('docum third')
        [(2, 2.5207), (0, 0.0), (1, 0.0)]
        """
        keywords = q.split(' ')

        # special cases
        for word in keywords:
            if word not in self.invertedLists:
                return []
        if len(keywords) == 0:
            return []
        if len(keywords) == 1:
            rawList = self.invertedLists[keywords[0]]
            sortdList = sorted(rawList, key=lambda x: -x[1])
            return sortdList[0:3]

        # actual intersecting
        list1 = self.invertedLists[keywords[0]]
        for i in range(1, len(keywords)):
            list2 = self.invertedLists[keywords[i]]
            list1 = self.merge(list1, list2)

        sortdList = sorted(list1, key=lambda x: -x[1])
        return sortdList[0:3]

if __name__ == '__main__':
    """ Answer user queries for a file given as command line parameter. """

    if len(sys.argv) != 2:
        print('Usage: python3 inverted_index.py <filename>')
        sys.exit()

    print('Building inverted index ...')
    fileName = sys.argv[1]
    with open(fileName) as f:
        ii = InvertedIndex(f, 1.75, 0.75)
    print('done')

    while True:
        queryLine = input('\nEnter a query (space separated keywords)\n> ')
        matches = ii.process_query(queryLine)
        for recId, score in matches:
            text = ii.records[recId]['line'].strip()
            for keyword in queryLine.split(' '):
                patt = r'\b(' + keyword + r')\b'
                text = re.sub(patt, '[32m\g<0>[0m', text)
            print('[1m[{0:.4f}][0m: {1}'.format(score, text))
