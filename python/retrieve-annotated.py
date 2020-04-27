#!/usr/bin/env python
"""
Program to retrieve the annotations from a server/project directory and store in a file that resembles an input
file, but with fields for the annotation by the annotator added.
For annotator N, this adds the fields:
annN_label: label assigned
annN_conf: confidence
annN_remarks: list of remarks
where the N in the field name is always two digits, e.g. ann02_label or ann13_conf
"""

import json
import argparse
import runutils
import glob
import os

def get_result_value(result):
    """
    Retrieve the result value from a result object, but make sure we either return the only value set
    or an empty string if the object is not what we expect.
    :param result:
    :return:
    """
    value = result.get("value")
    if value is None:
        return ""
    choices = value.get("choices")
    if choices is None:
        return ""
    if len(choices) == 0:
        return ""
    return choices[0]


def convert(item, annnr, file):
    logger = runutils.ensurelogger()
    newitem = {}
    newitem.update(item["data"])
    # make sure the fields for the annotator are not already there
    if newitem.get(f"ann{annnr:02d}_label") is not None:
        logger.error("Annotation from annotator {annnr} for label already present!")
        raise Exception("ERROR")
    if newitem.get(f"ann{annnr:02d}_conf") is not None:
        logger.error("Annotation from annotator {annnr} for conf already present!")
        raise Exception("ERROR")
    if newitem.get(f"ann{annnr:02d}_remarks") is not None:
        logger.error("Annotation from annotator {annnr} for remarks already present!")
        raise Exception("ERROR")
    newitem[f"ann{annnr:02d}_label"] = ""
    newitem[f"ann{annnr:02d}_conf"] = ""
    newitem[f"ann{annnr:02d}_remarks"] = ""
    compls = item.get("completions")
    if compls is None or len(compls) == 0:
        logger.info(f"No completions in file {file}, setting everything to missing")
        return newitem
    elif len(compls) > 1:
        logger.info(f"More than one completion in file {file} ({len(compls)}), using first")
    compl = compls[0]
    # now get the actual annotation data:
    results = compl.get("result")
    if results is None or len(results) == 0:
        logger.info(f"No result in file {file}, setting everything to missing")
        return newitem
    # process the results
    for result in results:
        name = result.get("from_name")
        if name == "label":
            newitem[f"ann{annnr:02d}_label"] = get_result_value(result)
        if name == "rating":
            newitem[f"ann{annnr:02d}_conf"] = get_result_value(result)
        if name == "remark":
            newitem[f"ann{annnr:02d}_remarks"] = "|".join(result["value"]["text"])
    return newitem


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("indir", help="Project directory")
    parser.add_argument("outfile", help="Output json file file (should have extension .json) and use proper name pattern")
    parser.add_argument("annnr", type=int, help="Annotator number of this project")
    args = parser.parse_args()

    logger = runutils.set_logger(args)
    runutils.run_start()

    completions = os.path.join(args.indir, "completions")
    completionspat = completions + "/*.json"
    files = glob.glob(completionspat)
    logger.info(f"Found {len(files)} annotations")
    if len(files) == 0:
        logger.error("No annotations found!")
        raise Exception("ERROR")
    data = []
    for file in files:
        with open(file, "rt", encoding="utf8") as infp:
            item = json.load(infp)
            try:
                item = convert(item, args.annnr, file)
                data.append(item)
            except Exception as e:
                logger.warn(f"Ignoring file {infp.name} because of {e}")
    with open(args.outfile, "wt", encoding="utf8") as outfp:
        json.dump(data, outfp)
    logger.info(f"Saved to file {args.outfile}")
    runutils.run_stop()
