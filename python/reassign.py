#!/usr/bin/env python
"""
Program to re-assign already annotated items to a new set of annotators.
This reads in the retrieved annotations from several annotators, combines them and assigns to
a list of annotators, trying to allocate the same number of items to each randomly, without
assigning an item to the same annotator twice.
"""

import json
import argparse
import runutils
import random
import sys
from collections import defaultdict, Counter


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--infiles", nargs="+", help="One or more files retrieved from their projects")
    parser.add_argument("--outpref", required=True, help="Output file prefix")
    parser.add_argument("--annotators", nargs="+", type=int, help="List of annotator ids to assign to")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("-d", action="store_true", help="Debug")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()
    random.seed(args.seed)

    # for each of the new annotator ids, store which object idxs have already been annotated by them
    per_annid = {}
    for annid in args.annotators:
        per_annid[annid] = set()
    # also keep track of how items get assigned from annotator to annotator
    old2new = defaultdict(Counter)
    new4old = defaultdict(Counter)

    # each object is added to this list and uniquely identified by the index in it
    all = []
    n_total = 0
    # First of all, read all objects from all the input files
    for infile in args.infiles:
        with open(infile, "rt", encoding="utf8") as reader:
            objs = json.load(reader)
            n_in = len(objs)
            n_total += n_in
            logger.info(f"Loaded {n_in} items from {infile}")
            for obj in objs:
                all.append(obj)
    # reshuffle the list of objects
    random.shuffle(all)

    # store all the indices of objects already seen by each of the new annotators
    for idx, obj in enumerate(all):
        assigned = obj["assigned"]
        for a in assigned:
            if a in per_annid:
                per_annid[a].add(idx)
    for annid,v in per_annid.items():
        logger.info(f"Items already seen by annotator {annid}: {len(v)}")
        logger.debug(f"Items ids seen by {annid}: {per_annid[annid]}")
    # Try to assign items in a round robin fashion randomly to each annotator
    # We want to choose for each annotator from all the items not already assigned to it and
    # once we have assigned an item, remove it from all the lists available to each annotator
    # Let's not be clever about this and brute force this: build the list available to an annotator each time we need it
    new_forann = {}
    for annid in args.annotators:
        new_forann[annid] = []
    iterations = 0
    while(True):
        iterations += 1
        logger.debug(f"Doing a new round: {iterations}")
        added = 0
        for annid in args.annotators:
            logger.debug(f"Assigning to annotator {annid}")
            available = []
            availableidxs = []
            logger.debug(f"Already used for {annid}: {per_annid[annid]}")
            for idx, obj in enumerate(all):
                if idx not in per_annid[annid]:
                    available.append(obj)
                    availableidxs.append(idx)
            logger.debug(f"Found available: {availableidxs}")
            if len(available) == 0:
                logger.debug("Nothing available not doing anything for this annotator")
                continue
            i = random.randint(0, len(availableidxs)-1)
            idx = availableidxs[i]
            obj = available[i]
            logger.debug(f"Randomly chosen {idx} out of {availableidxs}")
            # we need a copy of the object so we do not mess up the assigned status for everyone else!
            objcopy = obj.copy()
            assigneds = ",".join([str(x) for x in objcopy.get("assigned", ["NA"])])
            old2new[assigneds][annid] += 1
            new4old[annid][assigneds] += 1
            objcopy["assigned"].append(annid)
            new_forann[annid].append(idx)
            for a in args.annotators:
                per_annid[a].add(idx)
            added += 1
        logger.debug(f"End of round {iterations}: added={added}")
        for annid in args.annotators:
            logger.debug(f"Assigned to {annid} now: {new_forann[annid]}")
        if added == 0:
            break
        #if iterations == 2:
        #    break
    for annid in args.annotators:
        logger.info(f"Nr items assigned to new {annid} from old: {dict(new4old[annid])}")
    for annid in old2new.keys():
        logger.info(f"Nr items assigned from old {annid} to new: {dict(old2new[annid])}")
    for annid in args.annotators:
        logger.info(f"Items assigned to annotator {annid}: {len(new_forann[annid])}")
        logger.debug(f"Item ids: {new_forann[annid]}")
        filename = args.outpref + f"_ann{annid:02d}.json"
        with open(filename, "wt", encoding="utf8") as outfp:
            objs = []
            for idx in new_forann[annid]:
                objs.append(all[idx])
            json.dump(objs, outfp)
        logger.info(f"Set for annotator {annid} saved to {filename}")

    runutils.run_stop()