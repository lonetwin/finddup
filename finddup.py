#!/usr/bin/env python
import os
import sys
import re
import string
import hashlib
import argparse
from functools import partial

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
    readbytes = None if flsize < blocksize else blocksize
    with open(filename, 'rb') as fl:
        return hashlib.md5(fl.read(readbytes)).hexdigest()


def hash_fuzzy(ignored, name):
    """First ^normalize^ a filename and then return the md5 digest of the
    normalized name.

    Normalizing means:
        * converting the filename to lowercase & removing the extension
        * removing all spaces and punctuation in the filename
    """
    name, _ = os.path.splitext(name.lower())
    name = name.replace('&', 'and')
    name = name.translate(None, string.whitespace + string.punctuation)
    return hashlib.md5(name.encode('utf-8')).hexdigest()


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
    parser.add_argument('-e', '--exclude', default='(?!.*)',
                        help='exclude files where the path matches the provided regex pattern')
    parser.add_argument('-o', '--only', default='.*',
                        help='only consider files where the name matches the provided regex pattern')

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
        hash_fn = hash_fuzzy
    else: # args.name <- default
        hash_fn = lambda _, name: name

    path_pattern = re.compile(args.exclude)
    name_pattern = re.compile(args.only)

    # - begin hashing
    file_hash = {}
    nfiles = 0
    for directory in args.DIRECTORIES:
        for root, subdirs, files in os.walk(directory):
            for name in filter(name_pattern.search, files):
                path = os.path.join(root, name)
                if path_pattern.search(path):
                    continue
                nfiles += 1
                file_hash.setdefault(hash_fn(root, name), []).append(path)

    dups = {k: v for k, v in file_hash.items() if len(v) > 1}
    for k, v in dups.items():
        print('%s\n\t%s' % (k, '\n\t'.join(sorted(v))))

    if dups:
        print('\nProcessed {} files and found {} possible duplicates'.format(nfiles, len(dups)))
    else:
        print('\nProcessed {} files and found no duplicates'.format(nfiles))

if __name__ == '__main__':
    main()
