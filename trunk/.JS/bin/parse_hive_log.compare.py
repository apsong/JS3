#! /usr/bin/env python
from __future__ import print_function
import sys, datetime
import fileinput, re

print(sys.argv[1:])
max = len(sys.argv)-1
stats = {}
for line in fileinput.input():
    (num, s, key) = line.split("\t")
    #if re.match("LOAD|\[SUMMARY\]", key):
    #    continue
    num = int(num)/1000
    if (key not in stats):
        stats[key] = [num]
    else:
        stats[key].append(num)

    if (len(stats[key]) == max):
        num0 = stats[key][0]
        print("%8d " % num0, end="")
        for num in stats[key][1:]:
            s = "%d" % (num-num0)
            if num > num0:
                s = "+" + s
            print("%8s " % s, end="")
        print(key, end="")
