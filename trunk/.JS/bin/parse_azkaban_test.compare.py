#! /usr/bin/env python
from __future__ import print_function
import sys, datetime
import fileinput, re

max=6
stats = {}
for line in fileinput.input():
    lst = line.split()
    if len(lst) != 3:
        continue
    (num, unit, key) = lst
    if not re.match("^[KMG]$", unit):
        continue
    num = float(num)
    if (key not in stats):
        stats[key] = [num]
    else:
        stats[key].append(num)

    if (len(stats[key]) == max):
        num0 = stats[key][0]
        print("%8.1f %s  " % (num0, unit), end="")
        for num in stats[key][1:]:
            s = "%.1f %s" % (num-num0, unit)
            if num > num0:
                s = "+" + s
            print("%8s " % s, end="")
        print(key)
