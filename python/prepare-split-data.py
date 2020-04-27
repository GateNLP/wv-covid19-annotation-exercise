#!/usr/bin/env python
"""
Program to convert the original data to what we need and group items into sets of k in separate files.
Each file with k items can then be subsequently get assigned to some annotator (see prepare-assign-data.py)
We keep all input fields and add the field "html" (the text to present) and the field "assigned" (list of set numbers
0..(k-1) this item is/has been assigned to, this list is empty initially)
Major steps:
* read all data, but filter items with missing data fields, abort if major problem
* shuffle, using the random seed
* if --skip, ignore that many items at the beginning (maybe already used)
* split the rest into as many sets of -s as possible or take -n sets if specified
* NOTE: ignore any items at the end which would not make up a complete set
* store all the sets using the output file prefix, nubering the sets starting with 0
"""

import json
import argparse
import runutils
import random
import regex
import gzip

REQ_FIELDS = ["Claim", "Explaination", "Link", "Source", "Source_Lang", "Date", "Country", "Factcheck_Org", "Label"]
TEMPLATE = """
  <div><font size="+2"><b>Claim:</b>{0}</font></div>
  <p>
  <b>Explanation:</b>{1}
  <p>
  <a href="{2}" target="_blank">{2}</a> 
"""

PAT_WS = regex.compile(r"\s\s+")


def check(indata, n):
    """
    Check if the item is useful/valid.
    :param indata: the item object
    :return: the item or None if not valid
    """
    logger = runutils.ensurelogger()
    have_error = False
    if 'Source_Lang_New' in indata:
        indata['Source_Lang'] = indata['Source_Lang_New']
    for k in REQ_FIELDS:
        val = indata.get(k)
        if not val:
            logger.warning(f"Input object {n}: field {k} is missing or empty, item skipped")
            have_error = True
    if have_error:
        return None
    else:
        return indata


def input2obj(indata, n):
    """
    Convert a single object from the input to what we need.
    NOTE: at this point we already expect the item to be valid!
    NOTE: if this encounters an error it should return None to indicate that the item should get skipped
    :param indata: a single item as read from the input
    :return: converted item
    """
    # for now we keep all the original data and just add an additional field "html" with the data we need to present
    claim = PAT_WS.sub(" ", indata["Claim"])
    expl = PAT_WS.sub(" ", indata["Explaination"])
    src = indata["Source"]
    html = TEMPLATE.format(claim, expl, src)
    indata["html"] = html
    return indata


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input JOSN/JSONL file")
    parser.add_argument("--fmt", type=str, default="json", help="Input format (json, jsonl), default is json")
    parser.add_argument("outpref", help="Output file prefix, e.g. dirname/filepref")
    parser.add_argument("-s", type=int, default=25, help="Size (number of items) of each set (25)")
    parser.add_argument("-n", type=int, default=None, help="Number of sets to take (after optional skip), default: as many as possible")
    parser.add_argument("--skip", type=int, default=0, help="Number of items to skip after shuffling before taking rest or n")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()

    # this will contain the objects as we need them for the annotation (fields already selected/converted)
    objs = []
    n_in = 0
    n_skipped = 0
    if args.infile.endswith(".gz"):
        myopen = gzip.open
    else:
        myopen = open
    if args.fmt == "jsonl":
        with myopen(args.infile, "rt", encoding="utf8") as reader:
            for line in reader:
                n_in += 1
                obj = json.loads(line)
                objs.append(obj)
    elif args.fmt == "json":
        with myopen(args.infile, "rt", encoding="utf8") as reader:
            objs = json.load(reader)
            n_in = len(objs)
    else:
        raise Exception(f"Not a valid format: {args.fmt}")

    objsread = objs
    objs = []
    n_non_en = 0
    for idx, obj in enumerate(objsread):
        obj = check(obj, idx)
        if not obj:
            n_skipped += 1
        else:
            # check if we got the correct language
            if obj["Source_Lang"] != "en":
                n_non_en += 1
                n_skipped += 1
                continue
            obj = input2obj(obj, idx)
            if not obj:
                n_skipped += 1
            else:
                objs.append(obj)

    n_ok = len(objs)
    # now shuffle the objects
    random.seed(args.seed)
    random.shuffle(objs)

    if args.skip:
        if args.skip < n_ok:
            objs = objs[args.skip:]
            logger.info(f"Skipping {args.skip}, got {len(objs)} remaining")
        else:
            logger.error(f"Not enough input data to skip {args.skip}, only have {n_ok}")
            raise Exception("Not enough data")
    n_considered = len(objs)
    if n_considered < args.s:
        logger.error(f"Got only {n_considered} items, cannot proceed to make at least one set of size {args.s}")
        raise Exception("Not enough data")
    # args.n: number of sets requested
    # n: number of sets we take
    if args.n:
        if (args.n * args.s) > n_considered:
            logger.error(f"Requested {args.n} sets, but only got {n_considered} items")
            raise Exception("Not enough data")
        n = args.n
        nitems = args.n * args.s
        remainder = objs[nitems:]
        objs = objs[:nitems+1]
    else:
        n = int(n_considered / args.s)
        nitems = n * args.s
        remainder = objs[nitems:]
        objs = objs[:nitems+1]
    logger.info(f"Creating {n} sets of size {args.s}, total of {nitems} items")

    n_total = 0
    for setnr in range(n):
        fromidx = int(setnr*args.s)
        toidx = int(fromidx + args.s )
        # logger.info(f"DEBUG: trying to get indices {fromidx} to {toidx}")
        items = objs[fromidx:toidx]
        fname = args.outpref + "_" + f"set{setnr:03d}" + ".json"
        n_total = n_total + len(items)
        # add the assignment index as a field
        for item in items:
            item["assigned"] = []
        with open(fname, "wt", encoding="utf8") as outfp:
            json.dump(items, outfp)
            logger.info(f"Wrote file {fname} containing {len(items)} items")
    # OK on second thought, also output anything that may be left over
    for item in remainder:
        item["assigned"] = []
    fname = args.outpref + "_" + f"remaining" + ".json"
    with open(fname, "wt", encoding="utf8") as outfp:
        json.dump(remainder, outfp)
        logger.info(f"Wrote file {fname} containing remaining {len(remainder)} items")

    logger.info(f"Total number of items read:    {n_in}")
    logger.info(f"Number of items skipped:       {n_skipped}")
    logger.info(f"       of which non-en:        {n_non_en}")
    logger.info(f"Number of items ok:            {n_ok}")
    logger.info(f"Number of sets created:        {n}")
    logger.info(f"Number of items in all sets:   {n_total}")
    logger.info(f"Number of items in remaining:  {len(remainder)}")
    logger.info(f"Number of items total:         {len(remainder)+n_total}")
    runutils.run_stop()
