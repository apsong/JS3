#! /usr/bin/env python3.4

import threading, logging
import json, random
import argparse

parser = argparse.ArgumentParser(description='Start threads to doc.query repeately.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-t', '--threads', type=int, required=True)
parser.add_argument('-n', '--times', type=int, default=-1, help='times')
parser.add_argument('-x', action='store_true')
parser.add_argument('-y', action='store_true')
parser.add_argument('-xy', action='store_true')
NS=parser.parse_args()
print(NS)
print(NS.threads, NS.times, NS.x, NS.y)

