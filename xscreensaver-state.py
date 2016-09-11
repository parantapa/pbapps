#!/usr/bin/env python2
# encoding: utf-8
"""
Display if xscreensaver is running.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
import subprocess as sub

from pbapps_common import do_main, COLORS, ICONS

MODULE = "xscreensaver-state"

def get_xscreensaver_status(devnull):
    """
    Check if xscreensaver is running
    """

    try:
        cmd = ["xscreensaver-command", "-version"]
        sub.check_call(cmd, stdout=devnull, stderr=devnull)

        color = COLORS.green
    except sub.CalledProcessError:
        color = COLORS.red

    return [{
        "name": MODULE,
        "full_text": ICONS.fa_times,
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
