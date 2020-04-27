#!/usr/bin/env python
"""
Script to convert a file from JSONL format (one map per line) to JSON format (an array of maps)
"""

import json
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("infile", help="Input JOSNL file")
parser.add_argument("outfile", help="Output JOSN file")
args = parser.parse_args()

objs = []
n = 0
with open(args.infile, "rt", encoding="utf8") as reader:
    for line in reader:
        n += 1
        obj = json.loads(line)
        objs.append(obj)

with open(args.outfile, "wt", encoding="utf8") as writer:
    json.dump(objs, writer)

print(f"Converted {n} lines")


