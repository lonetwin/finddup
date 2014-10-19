finddup
=======

Command to find duplicate files under a set of directories (using name, _fuzzy name_ or md5 checksum matches)

Examples:
```
  # find duplicates using md5 checksums of the first 4k bytes of files under /home/foobar
  $ python finddup.py -m /home/foobar


  # find duplicates using md5 checksums of the first 8k bytes of file under /home/foo and
  # /home/bar
  $ python finddup.py -m -b 8k /home/foo /home/bar

  # find duplicates by 'fuzzy' matching the names of files under /home/foo and /home/bar
  # and /tmp/baz
  $ python finddup.py -f /home/foo /home/bar /tmp/baz

  # find duplicates by matching the exact names of files under /home/foo and /home/bar and
  # /tmp/baz
  $ python finddup.py /home/foo /home/bar /tmp/baz
```

If you find this useful, or have comments/suggestions, please let me know.
