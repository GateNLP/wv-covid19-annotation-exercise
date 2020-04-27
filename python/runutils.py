#!/usr/bin/env python
"""
Utilities for running code: logging, timing/benchmarking.
Author: Johann Petrak
"""
import sys
import logging
import datetime
import time

logger = None
start = 0


def set_logger(args=None, name=None, file=None):
    """
    Set up logger for the module "name". If file is given, log to that file as well.
    If file is not given but args is given and has "outpref" parameter, log to
    file "outpref.DATETIME.log" as well.
    :param name: name to use in the log, if None, uses sys.argv[0]
    :param file: if given, log to this destination in addition to stderr
    :param args: if given, an argparser namespace, checks for: "d" and "outpref"
    :return: the logger instance
    """
    global logger
    if name is None:
        name = sys.argv[0]
    if logger:
        raise Exception("Odd, we should not have a logger yet?")
    logger = logging.getLogger(name)
    if args and hasattr(args, "d") and args.d:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO
    logger.setLevel(lvl)
    fmt = logging.Formatter('%(asctime)s|%(levelname)s|%(name)s|%(message)s')
    hndlr = logging.StreamHandler(sys.stderr)
    hndlr.setFormatter(fmt)
    logger.addHandler(hndlr)
    if not file and args and hasattr(args, "outpref"):
        dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file = args.outpref+f".{dt}.log"
    if file:
        hdnlr = logging.FileHandler(file)
        hndlr.setFormatter(fmt)
        logger.addHandler(hdnlr)
    logger.info("Started: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M%S")))
    if args:
        logger.info("Arguments: {}".format(args))
    return logger


def ensurelogger():
    """
    Make sure the global logger is set to some logger. This should not be necessary
    if the set_logger function is properly used, but guards against situations where
    functions that require a logger are used without proper setting up the logger.
    :return: global logger
    """
    global logger
    if not logger:
        logger = logging.getLogger("UNINITIALIZEDLOGGER")
    return logger


def run_start():
    """
    Define time when running starts.
    :return: system time in seconds
    """
    global start
    start = time.time()
    return start


def run_stop():
    """
    Log and return formatted elapsed run time.
    :return: tuple of formatted run time, run time in seconds
    """
    logger = ensurelogger()
    if start == 0:
        logger.warning("Run timing not set up properly, no time!")
        return "",0
    stop = time.time()
    delta = stop - start
    deltastr = str(datetime.timedelta(seconds=delta))
    logger.info(f"Runtime: {deltastr}")
    return deltastr, delta
