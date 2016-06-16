#!/usr/bin/env python2
# encoding: utf-8
"""
Display the system usage.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
from datetime import datetime

import psutil

from pbapps_common import do_main

MODULE = "sys-state"

C_GREY = "#7e8e91"
C_WHITE = "#f8f8f2"
C_RED = "#f92672"
C_GREEN = "#a6e22e"

SYMB_MEMORY = "\uf1c0"
SYMB_CPU = "\uf108"

def get_date():
    """
    Get date.
    """

    now = datetime.now()
    now = now.strftime("%a, %b %d %Y %I:%M:%S %p")

    return [{
        "name": "date",
        "instance": "date",
        "full_text": now
    }]

def get_cpuusage():
    """
    Get the cpu usage.
    """

    usages = psutil.cpu_percent(None, True)

    avg_usage = sum(usages) / len(usages)

    color = C_RED if avg_usage >= 80 else C_GREEN

    usages = [min(99.0, u) for u in usages]
    usages = ["{:2.0f}%".format(u) for u in usages]
    usages = " ".join(usages)

    return [{
        "name": "cpu_usage",
        "instance": 0,
        "full_text": "{} {}".format(SYMB_CPU, usages),
        "color":  color
    }]

def get_memusage():
    """
    Get the memory usage.
    """

    mem = psutil.virtual_memory()
    usage = min(99.0, mem.percent)

    return [{
        "name": "mem_usage",
        "instance": 0,
        "full_text": "{} {:2.0f}%".format(SYMB_MEMORY, usage),
        "color": C_GREEN if usage < 80 else C_RED
    }]

def blocks_iter():
    while True:
        blocks = []

        blocks.extend(get_memusage())
        blocks.extend(get_cpuusage())
        blocks.extend(get_date())

        yield blocks

        time.sleep(1)

def main():
    do_main(MODULE, 90, blocks_iter())

if __name__ == '__main__':
    main()
