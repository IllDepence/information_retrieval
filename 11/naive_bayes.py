"""
Copyright 2017, University of Freiburg.

Elmar Haussmann <haussmann@cs.uni-freiburg.de>
Patrick Brosi <brosi@cs.uni-freiburg.de>
"""

import re
import sys

_EPSILON = .1


class NaiveBayes():

    def __init__(self, filename):
        """
        Create NaiveBayes instance given a training file.

        >>> nb = NaiveBayes("example.txt")
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
                self.c[label]['docCount'] += 1
                for w in words:
                    if w not in self.c[label]['nwcs']:
                        self.c[label]['nwcs'][w] = 0
                    self.c[label]['nwcs'][w] += 1
                    self.c[label]['nc'] += 1
                    vocab.append(w)
                documentCount += 1

        vocabSize = len(set(vocab))

        for label, val in self.c.items():
            self.c[label]['pc'] = self.c[label]['docCount'] / documentCount
            for w, cnt in self.c[label]['nwcs'].items():
                self.c[label]['pwcs'][w] = (cnt + _EPSILON) /\
                                (self.c[label]['nc'] + _EPSILON * vocabSize)

    def predict(self):
        """
        Predict a label for each example in the document-term matrix,
        based on the learned probabities stored in this class.

        Return a list of predicted label ids.

        >>> # wv, cv = generate_vocab("example.txt")
        >>> # X, y = read_labeled_data("example.txt", cv, wv)
        >>> # nb = NaiveBayes()
        >>> # nb.train(X, y)
        >>> # X_test, y_test = read_labeled_data("example_test.txt", cv, wv)
        >>> # nb.predict(X_test)
        >>> #     array([0, 1])
        >>> # nb.predict(X)
        >>> #     array([0, 0, 1, 0, 1, 1])
        """

        return None  # TODO!

    def evaluate(self):
        """
        Predict the labels of X and print evaluation statistics.
        """

        # TODO!


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 naive_bayes.py <train-input> <test-input>")
        exit(1)

    # do training on training dataset

    # run the evaluation on the test dataset

    # print the 30 words with the highest p_wc values per class

if __name__ == '__main__':
    main()
