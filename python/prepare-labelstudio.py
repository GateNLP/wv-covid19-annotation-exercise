#!/usr/bin/env python
"""
Program to prepare the labelstudio projects.
The default parameters assume the program is run from the root directory of the repo.
"""

import json
import argparse
import runutils
import os
import regex
import glob

DEFAULT_ANNGUIDE_HTML = "annotation-guidelines.html"
DEFAULT_CONFIG = "label-studio/tmpl_config.xml"
TITLE = "WeVerify Covid-19 Annotation Exercise"

DEFAULT_GUIDE_URL = "https://gate.ac.uk/wiki/wv-covid19/annotation-guidelines.html"

TMPL_INIT_CMD = "label-studio init -l {0} -i {1} --input-format json  {2}"
PAT_WS = regex.compile(r"\s\s+")

def infilename(pref, i):
    infilepat = args.inpref + "*_" + f"ann{i:02d}" + ".json"
    infiles = glob.glob(infilepat)
    if len(infiles) != 1:
        logger.error(f"Not exactly one file for {infilepat} but {len(infiles)}")
        raise Exception("ERROR")
    infile = infiles[0]
    return infile

def projdirname(pref, i):
    return pref + f"_{i}"


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("inpref", help="Input data file prefix (without the _annN.json part")
    parser.add_argument("outpref", help="Output directory prefix e.g. label-studio/project-round1")
    parser.add_argument("-k", type=int, required=True, help="Number of sets/annotators")
    parser.add_argument("-p", type=int, default=9000, help="Starting port number (9000)")
    parser.add_argument("-c", type=str, default=DEFAULT_CONFIG, help=f"Config file template ({DEFAULT_CONFIG})")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()

    # read in the annotation guidelines HTML
    # NOTE: NOT NECESSARY
    #with open(DEFAULT_ANNGUIDE_HTML, "rt", encoding="utf8") as infp:
    #    guide_html = infp.read()
    #    guide_html = PAT_WS.sub(" ", guide_html)

    # check that all the input files are there and the project directories are not there
    infiles = []
    for i in range(args.k):
        infile = infilename(args.inpref, i)
        outdir = projdirname(args.outpref, i)
        if not os.path.exists(infile):
            raise Exception(f"Input file {infile} does not exist")
        if os.path.exists(outdir):
            raise Exception(f"Output directory {outdir} must not exist")

    for i in range(args.k):
        outdir = projdirname(args.outpref, i)
        infile = infilename(args.inpref, i)
        cmd = TMPL_INIT_CMD.format(args.c, infile, outdir)
        logger.info(f"Trying to create label-studio project {i}")
        logger.info(f"Running command: {cmd}")
        ret = os.system(cmd)
        if ret != 0:
            raise Exception(f"Something went wrong, got exit code {ret}")
        # if success, update the config json file of the project
        jfile = os.path.join(outdir, "config.json")
        with open(jfile, "rt", encoding="utf8") as infp:
            jconf = json.load(infp)
        # update the info we need to update:
        # NOTE: this does not work in label-studio anyways so we do not need to do that!
        # jconf["port"] = args.p + i
        # jconf["instruction"] = guide_html
        # jconf["title"] = TITLE
        with open(jfile, "wt", encoding="utf8") as outfp:
            jconf = json.dump(jconf, outfp)
        logger.info(f"Config file {jconf} updated")



    runutils.run_stop()
