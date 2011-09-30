#!/usr/bin/env python

import argparse
from collections import defaultdict
import logging
import nltk
from operator import itemgetter
import sys

logger = logging.getLogger(__name__)

named_entity_summary = {
    'LOCATION': defaultdict(int),
    'PERSON': defaultdict(int),
    'ORGANIZATION': defaultdict(int)
}

def extract_named_entities(filename):
    named_entities = named_entity_summary.copy()
    raw_text = open(filename).read();

    # tokenize the entire text into sentences
    for sentence in nltk.sent_tokenize(raw_text):
        logger.debug('sentence:\n%s' % sentence)
        # tokenize the sentence into words and tag parts of speech
        sentence_words = nltk.word_tokenize(sentence)
        # - using the nltk parts-of-speech tagger for now
        #  (other options may be faster/more accurate)
        pos_sentence = nltk.pos_tag(sentence_words)        
        logger.debug('parts of speech:\n%s' % pos_sentence)

        # use the nltk named-entity extractor
        tagged_tokens = nltk.ne_chunk(pos_sentence)
        # also availabe: batch_ne_chunk (tags tagged sentences)
        for tok in tagged_tokens.subtrees():
            # capture & tally any named entities
            if tok.node in named_entities.keys():
                val = ' '.join([val for val, type in tok.leaves()])
                logger.debug('%s: %s' % (tok.node, val))
                named_entities[tok.node][val] += 1

    # output any entities found & the count for each
    for ne_type in named_entities.keys():
        # skip any categories where no entities were found
        if not named_entities[ne_type]:
            continue
        
        print '\n%s:' % ne_type
        for name, count in sorted(named_entities[ne_type].iteritems(),
                                  key=itemgetter(1), reverse=True):
            print '%d\t%s' % (count, name)


def config_logging(level):
    # configure logger to be used for script output
    logger.setLevel(level)
    # customize log output slightly
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(level)
    # use custom simple formatter
    ch.setFormatter(SimpleFormatter())
    logger.addHandler(ch)
    # don't propagate to root logger
    logger.propagate = False


class SimpleFormatter(logging.Formatter):
    # simple log formatter - generally only displays the log message,
    # but for single-line messages with a log level greater than
    # logging.INFO, pre-pends the level name to the beginning of the
    # message.
    def __init__(self, fmt='%(message)s', datefmt=None):
        logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)

    def format(self, record):
        text = logging.Formatter.format(self, record)
        if record.levelno > logging.INFO and '\n' not in text:
            text = '%s: %s' % (record.__dict__['levelname'], text)
        return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract named entities from text.')
    parser.add_argument('files', metavar='FILE', nargs='+',
                        help='full path to the file(s) to be processed')
    parser.add_argument('--loglevel', metavar='loglevel', required=False,
                        choices=['WARN', 'INFO', 'DEBUG'], default='WARN',
                        help='Log level for additional output.')
    args = parser.parse_args()
    # configure logging
    config_logging(getattr(logging, args.loglevel))
        
    for file in args.files:
        print >> sys.stderr,  'Processing %s' % file
        extract_named_entities(file)
        print >> sys.stderr, '\n'
