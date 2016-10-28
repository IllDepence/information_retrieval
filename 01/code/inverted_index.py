"""
Copyright 2016 Tarek Saier <tarek.saier@uranus.uni-freiburg.de>

This work is free. You can redistribute it and/or modify
it under the terms of the WTFPL, Version 2, as published
by Sam Hocevar. See the COPYING file for more details.
"""

import re
import sys


class InvertedIndex:
    """ Class for creating an inverted index based a text file w/ one entry per
    line. """

    def __init__(self, fileObj):
        r""" Create inverted index given a file object.

        >>> import io
        >>> f = io.StringIO('Foo doc doc.\nBar doc.\nBaz doc.')
        >>> ii = InvertedIndex(f)
        >>> sorted(ii.invertedLists.items())
        [('Bar', [1]), ('Baz', [2]), ('Foo', [0]), ('doc', [0, 1, 2])]
        """

        self.invertedLists = {}
        self.records = []
        recordId = 0
        for line in fileObj:
            self.records.append(line)
            uniqueWords = []
            for word in re.split('\W+', line):
                if len(word) > 0:
                    if word not in self.invertedLists:
                        self.invertedLists[word] = []
                    if word not in uniqueWords:
                        self.invertedLists[word].append(recordId)
                        uniqueWords.append(word)
            recordId += 1

    def intersect(self, list1, list2):
        r""" Compute the intersection of two sorted inverted lists.

        >>> import io
        >>> ii = InvertedIndex(io.StringIO(''))
        >>> ii.intersect([0, 1, 2, 3], [0, 3])
        [0, 3]
        """

        if len(list1) == 0 or len(list2) == 0:
            return []

        idx1 = 0
        idx2 = 0
        reachedEnd = False
        result = []
        while not reachedEnd:
            advace1 = False
            advace2 = False
            curr1 = list1[idx1]
            curr2 = list2[idx2]
            reachedEnd1 = (list1[-1] == curr1)  # safe b/c record IDs are uniqe
            reachedEnd2 = (list2[-1] == curr2)

            if curr1 == curr2:  # match :)
                if curr1 not in result:
                    result.append(curr1)
                advace1 = True
                advace2 = True
            elif curr1 < curr2:
                advace1 = True
            else:
                advace2 = True

            if advace1:
                if reachedEnd1:       # Only higher record IDs w/o matches left
                    reachedEnd = True
                else:
                    idx1 += 1
            if advace2:
                if reachedEnd2:
                    reachedEnd = True
                else:
                    idx2 += 1

        return result

    def query(self, keywords):
        r""" Given a list of keywords, compute the list of record IDs that
        contains all of them.

        >>> import io
        >>> f = io.StringIO('a b c d\na b d\na c f d\na bc d')
        >>> ii = InvertedIndex(f)
        >>> ii.query(['a', 'c', 'd'])
        [0, 2]
        """

        # special cases
        for word in keywords:
            if word not in self.invertedLists:
                return []
        if len(keywords) == 0:
            return []
        if len(keywords) == 1:
            return self.invertedLists[keywords[0]]

        # actual intersecting
        list1 = self.invertedLists[keywords[0]]
        for idx in range(1, len(keywords)):
            list2 = self.invertedLists[keywords[idx]]
            list1 = self.intersect(list1, list2)
        return list1

if __name__ == '__main__':
    """ Answer user queries for a file given as command line parameter. """

    if len(sys.argv) != 2:
        print('Usage: python3 inverted_index.py <filename>')
        sys.exit()

    print('Building inverted index ...')
    fileName = sys.argv[1]
    with open(fileName) as f:
        ii = InvertedIndex(f)
    print('done')

    while True:
        queryLine = input('\nEnter a query (space separated keywords)\n> ')
        q = queryLine.split(' ')
        matches = ii.query(q)
        maxResults = 3
        if len(matches) < maxResults:
            maxResults = len(matches)
        for i in range(maxResults):
            text = ii.records[matches[i]].strip()
            for keyword in q:
                patt = r'\b(' + keyword + r')\b'
                text = re.sub(patt, '[32m\g<0>[0m', text)
            print('[1mMatch #{0}[0m: {1}'.format(i+1, text))
