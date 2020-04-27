#!/usr/bin/env python
"""
Program to extract a csv from retrieved annotations after the second round so proper IAA can be calculated
This also calculates some basic IAA.
"""

import json
import argparse
import runutils
import random
import sys


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--infiles", nargs="+", help="One or more files retrieved from their projects")
    parser.add_argument("--outcsv", required=True, help="Output CSV file")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()

    all = []
    n_total = 0
    outfp = open(args.outcsv, "wt")
    ntotal = 0
    nequal = 0
    for infile in args.infiles:
        with open(infile, "rt", encoding="utf8") as reader:
            objs = json.load(reader)
            n_in = len(objs)
            n_total += n_in
            logger.info(f"Loaded {n_in} items from {infile}")
            # assign each item from the set to all annotators not already in the assigned list
            for i, obj in enumerate(objs):
                all.append(obj)
                # logger.info(f"DEBUG: checking object {i}")
                labels = []
                annotators = []
                # for each field in the object, check if it is a label annotation by some annotator
                for k in obj:
                    if k.endswith("_label") and k.startswith("ann"):
                        # logger.info(f"DEBUG: got label key: {k}")
                        l = obj.get(k)
                        if not l:
                            logger.warning(f"Empty label in file {infile} for item {i} of {len(objs)}, ignoring")
                            continue
                        a = k[:5]
                        labels.append(l)
                        annotators.append(a)
                if len(labels) != 2:
                    logger.warning(f"Not exactly two annotators in  {infile} for item {i} of {len(objs)} but {len(labels)}, ignoring")
                else:
                    ntotal += 1
                    # only consider/output the ones which have exactly two annotations
                    print(labels[0],labels[1],annotators[0],annotators[1], file=outfp, sep=",")
                    if labels[0] == labels[1]:
                        nequal += 1
    logger.info(f"Total annotation pairs: {ntotal}")
    logger.info(f"Equal annotation pairs: {nequal}")
    if ntotal > 0:
        logger.info(f"Equal proportion:       {nequal/ntotal}")
    runutils.run_stop()