#! /usr/bin/env python3.4

import logging
import json, random, os
import argparse
from pathlib import PosixPath

parser = argparse.ArgumentParser(description='Prepare directories and files for test',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('DIR_NUMS', type=int, default=10, nargs='+', help='number of directories per level')
parser.add_argument('FILE', choices=['1B.dat', '1K.dat', '1M.dat', '10M.dat', '100M.dat'])
parser.add_argument('-v', default=0, action='count', help='Verbose output. "-vv" is more than "-v"')
ARGS=parser.parse_args()

if ARGS.v>0:
    lvl=logging.DEBUG
else:
    lvl=logging.WARNING
logging.basicConfig(format=' [%(asctime)s.%(msecs)03d] %(message)s', datefmt='%H:%M:%S', level=lvl)
logging.warn(ARGS)

def mkdirs(bases, number):
    new_bases=[]
    format = "%%0%dd" % len("%d" % (number-1))
    for i in range(number):
        dir = os.path.join(random.choice(bases), format % i)
        logging.info("mkdir %s" % dir)
        PosixPath(dir).mkdir()
        new_bases.append(dir)
    logging.warn("mkdirs([%s - %s], %d) finished." % (bases[0], bases[-1], number))
    return new_bases

def mklinks(bases, number, filename):
    #new_bases=[]
    src_file = "/TEST/dat/%s" % filename
    format = "%%0%dd_%%s" % len("%d" % (number-1))
    for i in range(number):
        link = os.path.join(random.choice(bases), format % (i, filename))
        logging.info("ln -s %s %s" % (src_file, link))
        PosixPath(link).symlink_to(src_file)
        #new_bases.append(link)
    logging.warn("mklinks([%s - %s], %d, %s) finished." % (bases[0], bases[-1], number, filename))
    #return new_bases

dir_base="x".join(map(str, ARGS.DIR_NUMS)) + ("x%s" % os.path.splitext(ARGS.FILE)[0])

logging.warn("mkdir %s" % dir_base)
PosixPath(dir_base).mkdir()

bases=[dir_base]
for num in ARGS.DIR_NUMS[:-1]:
    bases=mkdirs(bases, num)
mklinks(bases, ARGS.DIR_NUMS[-1], ARGS.FILE)
