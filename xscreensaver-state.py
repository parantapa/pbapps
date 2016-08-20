#!/usr/bin/env python2
# encoding: utf-8
"""
Display if xscreensaver is running.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
import subprocess as sub

from pbapps_common import do_main

MODULE = "xscreensaver-state"

C_GREEN = "#a6e22e"
C_RED = "#f92672"

SYMB_XSCREENSAVER = "\uf00d"

def get_xscreensaver_status(devnull):
    """
    Check if xscreensaver is running
    """

    try:
        cmd = ["xscreensaver-command", "-version"]
        sub.check_call(cmd, stdout=devnull, stderr=devnull)

        color = C_GREEN
    except sub.CalledProcessError:
        color = C_RED

    return [{
        "name": MODULE,
        "full_text": SYMB_XSCREENSAVER,
        "color": color
        }]

def blocks_iter():
    null = open("/dev/null", "w")

    while True:
        yield get_xscreensaver_status(null)
        time.sleep(2)

def main():
    do_main(MODULE, 85, blocks_iter())

if __name__ == '__main__':
    main()
