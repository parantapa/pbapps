#!/usr/bin/env python2
# encoding: utf-8
"""
My status line program for i3bar.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
import sys
import json
import glob
import time
import codecs
from select import select, error as SelectError
import signal

import logbook
from pypb import register_exit_signals

from pbapps_common import get_i3status_rundir, \
                          get_rundir, \
                          get_logdir, \
                          dummy_handler

log = logbook.Logger("i3status")

def read():
    """
    Read a single JSON encoded line.
    """

    try:
        rl, _, _ = select([sys.stdin], [], [], 1.0)
        if not rl:
            return None
    except SelectError:
        return None

    inp = raw_input().strip()
    if inp == '[':
        return None

    inp = inp.strip(",")
    inp = json.loads(inp)
    return inp

def write(obj, hdr=False):
    """
    Write a single JSON encoded line.
    """

    if hdr:
        print(json.dumps(obj))
        sys.stdout.flush()
        return

    if obj is None:
        print("[")
        print("[]")
        sys.stdout.flush()
        return

    print("," + json.dumps(obj))
    sys.stdout.flush()

def get_pids(extdir):
    """
    Get the dict of service to process ids.
    """

    pid_fnames = glob.glob(extdir + "/*.pid")

    pids = {}
    for fname in pid_fnames:
        try:
            # Get the pid
            with open(fname, "r") as fobj:
                pid = fobj.read().strip()
            pid = int(pid)

            # Check if process running
            os.kill(pid, 0)
        except (OSError, IOError, ValueError):
            continue

        service = os.path.basename(fname)
        service = service.split(".")[0]
        pids[service] = pid

    return pids

def get_blocks(extdir):
    """
    Get the i3bar blocks.
    """

    block_fnames = glob.glob(extdir + "/*.block")

    blocks = {}
    for fname in block_fnames:
        try:
            # Get the json state
            with open(fname) as fobj:
                block = json.load(fobj)
        except (OSError, IOError, ValueError):
            continue

        if isinstance(block, list):
            pass
        elif isinstance(block, dict):
            block = [block]
        else:
            continue

        service = os.path.basename(fname)
        service = service.split(".")[0]
        blocks[service] = block

    return blocks

def read_blocks(extdir):
    """
    Read all the state and pid files.
    """

    pids = get_pids(extdir)
    blocks = get_blocks(extdir)

    services = sorted(pids)
    ret = []
    for service in services:
        if service not in blocks:
            continue

        blks = blocks[service]
        for i, blk in enumerate(blks):
            name = service
            instance = "{}-{}".format(service, i)

            blk.setdefault("name", name)
            blk.setdefault("instance", instance)
            blk.setdefault("full_text", "running")
            ret.append(blk)

    return ret

def main():
    # Setup logfile
    logfile = get_logdir() + "/i3status.log"
    logbook.FileHandler(logfile).push_application()

    with log.catch_exceptions():
        # Write out my own pid
        pidfile = get_rundir() + "/i3status.pid"
        with open(pidfile, "w") as fobj:
            fobj.write(str(os.getpid()))

        # Get the external state directory
        extdir = get_i3status_rundir()

        # Make stdin and stdout UTF-8
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
        sys.stdin = codecs.getreader("utf-8")(sys.stdin)

        # Setup dummy signal handler on SIGUSR1
        # Useful for waking up from sleep
        register_exit_signals()
        signal.signal(signal.SIGUSR1, dummy_handler)

        # Write out the header
        write({"version": 1, "click_events": True}, True)
        write(None)

        while True:
            # We ignore the input
            _ = read()
            write(read_blocks(extdir))
            time.sleep(5)

if __name__ == '__main__':
    main()
