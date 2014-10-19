#!/usr/bin/env python
import os
import sys
import re
import string
import hashlib
import argparse
from functools import wraps, partial

# borrowed from http://goo.gl/kFJZKb
# which originally borrowed from http://goo.gl/zeJZl
def human2bytes(s):
    """
    >>> human2bytes('1M')
    1048576
    >>> human2bytes('1G')
    1073741824
    """
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    letter = s[-1].strip().upper()
    num = s[:-1]
    if letter not in symbols:
        return -1
    try:
        num = float(num)
    except ValueError:
        return -1

    prefix = {symbols[0]: 1}

    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    return int(num * prefix[letter])


class HelpFormatterMixin(argparse.RawDescriptionHelpFormatter,
                         argparse.ArgumentDefaultsHelpFormatter): pass


def hash_md5(path, name, blocksize):
    """hash_md5(path, name, blocksize) -> <md5digest>

    Returns the md5 checksum of the file's first blocksize block
    """
    filename = os.path.join(path, name)
    if not os.path.isfile(filename):
        return 'NotARegularFile'
    flsize = os.stat(filename).st_size
    readbytes = flsize if flsize < blocksize else blocksize
    with open(filename, 'rb') as fl:
        return hashlib.md5(fl.read(readbytes)).hexdigest()


def hash_fuzzy():
    """Returns a function that will first ^normalize^ a filename and then
    return the md5 digest of the normalized name.

    Normalizing means:
        * converting the filename to lowercase
        * removing all spaces in the filename
        * replacing '&' with 'and' in the filename
        * removing all punctuation characters in the filename
    """
    punctuation_re = '|'.join(
            # - escape characters that have special meaning in regexs
            '%s%s' % ('' if char not in '.?+*|[]()$^\\' else '\\', char)
                for char in string.punctuation)

    def inner(path, name):
        name = name.lower()
        for pattern, substitution in ((' +', ''),           # remove spaces
                                      ('&', 'and'),         # replace & with 'And'
                                      (punctuation_re, ''), # remove punctuation
                                      ):
            name = re.sub(pattern, substitution, name)
        return hashlib.md5(name.encode('utf-8')).hexdigest()
    return inner


def main():
    parser = argparse.ArgumentParser(
                usage = "%s [OPTIONS] DIRECTORIES ..." % sys.argv[0],
                description = 'Find duplicate files within a list of directories',
                formatter_class = HelpFormatterMixin,
                epilog = (
                    "Example: find all likely duplicate files under the current\n"
                    "directory using the md5 checksums of the first 1K bytes of\n"
                    "the files to identify duplicates.\n"
                    "\t$ %s -m -b 1K ./") % sys.argv[0]
                )

    parser.add_argument('DIRECTORIES', nargs='+', help="directories to search")

    ex_group = parser.add_mutually_exclusive_group()

    ex_group.add_argument('-n', '--name', action="store_true", default=True,
            help="use exact filenames (fastest)")

    ex_group.add_argument('-f', '--fuzzy', action="store_true",
            help="use fuzzy match of file names")

    parser.add_argument('-m', '--md5', action="store_true",
            help="use md5 checksums (slowest)")

    ex_group.add_argument('-B', '--blocksize', default='4K',
            help="limit md5 checksums to first BLOCKSIZE bytes")

    args = parser.parse_args()

    blocksize = human2bytes(args.blocksize if args.blocksize else '4K')

    if args.md5:
        hash_fn = partial(hash_md5, blocksize=blocksize)
    elif args.fuzzy:
        hash_fn = hash_fuzzy()
    else: # args.name <- default
        hash_fn = lambda path, name: name

    # - begin hashing
    file_hash = {}
    nfiles = 0
    for directory in args.DIRECTORIES:
        for root, subdirs, files in os.walk(directory):
            nfiles += 1
            for name in files:
                file_hash.setdefault(hash_fn(root, name), []).append(os.path.join(root, name))

    for k, v in file_hash.items():
        if len(v) > 1:
            print('%s\n\t%s' % (k, '\n\t'.join(sorted(v))))

    print('\nProcessed {} files and found {} possible duplicates'.format(nfiles, len(file_hash)))

if __name__ == '__main__':
    main()