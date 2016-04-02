#!/usr/bin/env python2
# encoding: utf-8
"""
Display state of git repos.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
import subprocess as sub

from pypb import abspath
from pbapps_common import do_main

MODULE = "git-multi-status"

C_WHITE = "#f8f8f2"
C_RED = "#f92672"

REPO_DIRS = abspath("~/.repo-dirs")

def get_git_status():
    """
    Get git status.
    """

    with open(REPO_DIRS, "r") as fobj:
        lines = fobj.readlines()
    lines = [l.strip() for l in lines]
    lines = [l for l in lines if l]

    cmd = ["git-multi-status"] + lines
    try:
        status = sub.check_output(cmd).strip()
    except sub.CalledProcessError:
        status = None

    if status is None:
        return [{
            "name": MODULE,
            "instance": MODULE,
            "full_text": "??",
            "color": C_RED
        }]
    else:
        return [{
            "name": MODULE,
            "instance": MODULE,
            "full_text": status,
            "color": C_WHITE
        }]

def blocks_iter():
    while True:
        yield get_git_status()
        time.sleep(2)

def main():
    do_main(MODULE, 15, blocks_iter())

if __name__ == '__main__':
    main()
