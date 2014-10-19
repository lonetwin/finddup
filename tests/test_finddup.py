#!/usr/bin/env python
from unittest import TestCase

from finddup import (human2bytes,
                     hash_fuzzy,
                    )

class TestFinddup(TestCase):
    def test_human2bytes(self):
        test_data = { '1k'   : 1024,
                      '1.5K' : 1536,
                      '2m'   : 2097152,
                      '2.5M' : 2621440
                      }

        for s, v in test_data.items():
            self.assertEqual(human2bytes(s), v)

    def test_hash_fuzzy(self):
        similar_files = [('A file.txt', 'a File.txt'),
                         ("Good ol' tune.mp3", 'good_ol_tune.mp3'),
                         ('What is love?.flac', 'what-is-love.flac'),
                        ]

        for first, second in similar_files:
            self.assertEqual( hash_fuzzy('/', first), hash_fuzzy('/a/', second) )


