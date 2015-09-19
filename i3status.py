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
from select import select
import signal

def read():
    """
    Read a single JSON encoded line.
    """

    rl, _, _ = select([sys.stdin], [], [], 1.0)
    if not rl:
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

def dummy_handler(signum, frame): # pylint: disable=unused-argument
    """
    Dummy signal handler.
    """

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
    # Make stdin and stdout UTF-8
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
    sys.stdin = codecs.getreader("utf-8")(sys.stdin)

    # Create the external state directory
    uid = os.environ["UID"]
    uid = int(uid)
    extdir = "/run/user/{}/pbapps/i3status/external"
    extdir = extdir.format(uid)
    if not os.path.exists(extdir):
        os.makedirs(extdir, 0o700)

    # Write out my own pid
    pidfile = "/run/user/{}/pbapps/i3status/i3status.pid"
    pidfile = pidfile.format(uid)
    with open(pidfile, "w") as fobj:
        fobj.write(str(os.getpid()))

    # Setup dummy signal handler on SIGUSR1
    # Useful for waking up from sleep
    signal.signal(signal.SIGUSR1, dummy_handler)

    # Write out the header
    write({"version": 1, "click_events": True}, True)
    write(None)

    while True:
        # We ignore the input
        _ = read()
        write(read_blocks(extdir))
        time.sleep(1)

if __name__ == '__main__':
    main()
