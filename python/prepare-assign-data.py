#!/usr/bin/env python
"""
Program to assign k sets/files to k annotators in sequence.
Annotators are assigned from 0 to k-1
Input files need to all have names someprefix_setNNN*.json.
Output files will have names outprefix_setNNN_annMM.json
Each set is assigned to a different annotator
"""

import json
import argparse
import runutils
import glob

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inpref", help="Input file name prefix, same as output prefix of prepare-split-data")
    parser.add_argument("outpref", help="Output file prefix")
    parser.add_argument("fromsetnr", type=int, help="Number of first set to take")
    parser.add_argument("--fromannnr", type=int, default=0, help="Number of first annotator to assign to (0)")
    parser.add_argument("n", type=int, help="Number of sets to take")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()

    for i, setnr in enumerate(range(args.fromsetnr, args.fromsetnr+args.n)):
        annnr = i + args.fromannnr
        files = glob.glob(args.inpref+f"_set{setnr:03d}*.json")
        if len(files) != 1:
            logger.error(f"Could not find exactly one match for set {setnr} but {len(files)}")
            raise Exception("No proper intput")
        file = files[0]
        with open(file, "rt", encoding="utf8") as infp:
            data = json.load(infp)
        # add the annotator id to the field assigned
        for item in data:
            item["assigned"].append(annnr)
        # save to the output file
        outfile = args.outpref + f"_set{setnr:03d}_ann{annnr:02d}.json"
        with open(outfile, "wt", encoding="utf8") as outfp:
            json.dump(data, outfp)
        logger.info(f"File {file} assigned to annotator {annnr} and saved to {outfile}")
    runutils.run_stop()