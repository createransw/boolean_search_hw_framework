#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import codecs
import sys
from nltk.stem import SnowballStemmer

import json
import string



class Index:
    def __init__(self, index_file):
        stemmer = SnowballStemmer("russian")
        
        self.index: dict[str, set[str]] = {}
        f = codecs.open(index_file, encoding="utf-8", mode="r")

        for ln in f:
            sentence = ln.strip().translate(str.maketrans(string.punctuation, ' '*len(string.punctuation))).split()
            for i in range(1, len(sentence)):
                word = stemmer.stem(sentence[i].lower())
                if word not in self.index:
                    self.index[word] = set[str]()

                self.index[word].add(sentence[0])
                
        f.close()


class QueryTree:
    def __init__(self, qid, query):
        self._stemmer = SnowballStemmer("russian")
        self._request: list[str] = []

        tmp = ""

        for c in query.lower():
            match c:
                case " " | "(" | ")" | "|":
                    if len(tmp) > 0:
                        self._request.append(tmp)

                    tmp = ""
                    self._request.append(str(c))
                    
                case other:
                    tmp += c

        if len(tmp) > 0:
            self._request.append(tmp)


    def _get(self):
        if self._i < len(self._request):
            self._c = self._request[self._i]
            self._i += 1
        else:
            self._c = "!"

    def search(self, index):
        self._i = 0
        self._get()

        result = self._or(index)

        f = codecs.open("res.json", encoding="utf-8", mode="a")
        json.dump(list(result), f)

        
        return result

    def _or(self, index):
        result = self._and(index)

        while self._c == "|":
            self._get()
            result = result | self._and(index)

        return result

    def _and(self, index):
        result = self._token(index)

        while self._c == " ":
            self._get()
            result = result & self._token(index)

        return result
        

    def _token(self, index):
        result = set()
        
        if self._c == "(":
            self._get()
            result = self._or(index)
            if self._c != ")":
                raise ValueError('Unmatched bracket')
        else:
            if self._stemmer.stem(self._c) in index.index:
                result = index.index[self._stemmer.stem(self._c)]

        self._get()
        
        return result
            


class SearchResults:
    def __init__(self):
        self._results = []
    def add(self, found):
        self._results.append(found)

    def print_submission(self, objects_file, submission_file):
        inp = codecs.open(objects_file, encoding="utf-8", mode="r")
        outp = codecs.open(submission_file, encoding="utf-8", mode="w")

        outp.write("ObjectId,Relevance\n")
        inp.readline()
        for ln in inp:
            pair = ln.strip().split(",")
            outp.write(f"{pair[0]},{int(pair[2] in self._results[int(pair[1]) - 1])}\n")
        


def main():
    # Command line arguments.
    parser = argparse.ArgumentParser(description='Homework: Boolean Search')
    parser.add_argument('--queries_file', required = True, help='queries.numerate.txt')
    parser.add_argument('--objects_file', required = True, help='objects.numerate.txt')
    parser.add_argument('--docs_file', required = True, help='docs.tsv')
    parser.add_argument('--submission_file', required = True, help='output file with relevances')
    args = parser.parse_args()

    # Build index.
    index = Index(args.docs_file)

    # Process queries.
    search_results = SearchResults()
    with codecs.open(args.queries_file, mode='r', encoding='utf-8') as queries_fh:
        for line in queries_fh:
            fields = line.rstrip('\n').split('\t')
            qid = int(fields[0])
            query = fields[1]

            # Parse query.
            query_tree = QueryTree(qid, query)

            # Search and save results.
            search_results.add(query_tree.search(index))

    # Generate submission file.
    search_results.print_submission(args.objects_file, args.submission_file)


if __name__ == "__main__":
    main()

