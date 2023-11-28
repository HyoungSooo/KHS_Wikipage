import csv
from kiwipiepy import Kiwi


def extraction_nouns(text):
    return Kiwi().tokenize(text)


def get_words(text):
    nouns = []
    res = extraction_nouns(text)
    for token, pos, _, _ in res:
        if len(token) != 1 and pos.startswith('N') or pos.startswith('SL'):
            nouns.append(token)
    return nouns
