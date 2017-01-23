"""
Copyright 2016 Tarek Saier <tarek.saier@uranus.uni-freiburg.de>

This work is free. You can redistribute it and/or modify
it under the terms of the WTFPL, Version 2, as published
by Sam Hocevar. See the COPYING file for more details.
"""

import math
import re
import sys

_EPSILON = .1


class NaiveBayes():

    def __init__(self, filename, test=False):
        """ Create a NaiveBayes instance given a training file.

        >>> nb = NaiveBayes("example.txt", True)
        >>> [val['pc'] for val in list(nb.c.values())]
        [0.5, 0.5]
        >>> print('{0:.3f}'.format(nb.c['A']['pwcs']['a']))
        0.664
        >>> print('{0:.3f}'.format(nb.c['A']['pwcs']['b']))
        0.336
        >>> print('{0:.3f}'.format(nb.c['B']['pwcs']['a']))
        0.335
        >>> print('{0:.3f}'.format(nb.c['B']['pwcs']['b']))
        0.665
        """

        self.test = test

        self.stopwords = []
        with open('stopwords_en.txt') as f:
            for line in f:
                self.stopwords.append(line.strip())

        self.c = {}  # classes
        vocab = []
        documentCount = 0

        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                label, text = parts[0], parts[1]
                if label not in self.c:
                    self.c[label] = {}
                    self.c[label]['nwcs'] = {}
                    self.c[label]['pwcs'] = {}
                    self.c[label]['nc'] = 0
                    self.c[label]['docCount'] = 0

                words = re.sub('\W+', ' ', text.lower()).split()
                if not self.test:
                    words = [w for w in words if w not in self.stopwords]
                self.c[label]['docCount'] += 1
                for w in words:
                    if w not in self.c[label]['nwcs']:
                        self.c[label]['nwcs'][w] = 0
                    self.c[label]['nwcs'][w] += 1
                    self.c[label]['nc'] += 1
                    vocab.append(w)
                documentCount += 1

        vocabSize = len(set(vocab))
        for label, cls in self.c.items():
            self.c[label]['pc'] = cls['docCount'] / documentCount
            for w, cnt in cls['nwcs'].items():
                self.c[label]['pwcs'][w] = (cnt + _EPSILON) /\
                                            (cls['nc'] + _EPSILON * vocabSize)

    def predict(self, filename):
        """ Predict a label for each document in the given test file.

        >>> nb = NaiveBayes("example.txt", True)
        >>> nb.predict("example_test.txt")
        >>> [val['predLabel'] for val in nb.predictions]
        ['A', 'B']
        >>> nb.predict("example.txt")
        >>> [val['predLabel'] for val in nb.predictions]
        ['A', 'A', 'B', 'A', 'B', 'B']
        """

        self.predictions = []

        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split('\t')
                realLabel, text = parts[0], parts[1]
                words = re.sub('\W+', ' ', text.lower()).split()
                if not self.test:
                    words = [w for w in words if w not in self.stopwords]
                prediction = None
                bestP = -sys.maxsize
                for label, cls in self.c.items():
                    prob = 0
                    for w in words:
                        if w in cls['pwcs']:
                            prob += math.log(cls['pwcs'][w])
                    prob += math.log(cls['pc'])
                    if prob > bestP:
                        prediction = label
                        bestP = prob
                predObj = {}
                predObj['doc'] = text
                predObj['realLabel'] = realLabel
                predObj['predLabel'] = prediction
                self.predictions.append(predObj)
                # pre eval code
                if 'testDocs' not in self.c[realLabel]:
                    self.c[realLabel]['testDocs'] = 0
                self.c[realLabel]['testDocs'] += 1
                if 'predDocs' not in self.c[prediction]:
                    self.c[prediction]['predDocs'] = 0
                self.c[prediction]['predDocs'] += 1
                if realLabel == prediction:
                    if 'rightPreds' not in self.c[realLabel]:
                        self.c[realLabel]['rightPreds'] = 0
                    self.c[realLabel]['rightPreds'] += 1

    def evaluate(self):
        """ Calculate and output evaluation.
        """

        for label, cls in self.c.items():
            print('\nClass {0} (p_c = {1:.3f})'.format(label, cls['pc']))
            precision = cls['rightPreds'] / cls['predDocs']
            recall = cls['rightPreds'] / cls['testDocs']
            fscore = (2 * precision * recall) / (precision + recall)
            print('  Precision: {0:.2f}%'.format(precision*100))
            print('  Recall: {0:.2f}%'.format(recall*100))
            print('  F-Score: {0:.2f}%'.format(fscore*100))
            bestWords = sorted(cls['pwcs'], key=cls['pwcs'].get, reverse=True)
            print('  Top 30 words: {0}'.format(', '.join(bestWords[0:30])))


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 naive_bayes.py <train-input> <test-input>")
        exit(1)

    nb = NaiveBayes(sys.argv[1])
    nb.predict(sys.argv[2])
    nb.evaluate()

if __name__ == '__main__':
    main()
