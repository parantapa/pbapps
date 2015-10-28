#!/usr/bin/env python2
# encoding: utf-8
"""
Put the system state in display.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
import json
import time
from datetime import datetime
import subprocess as sub

import psutil
import pypb.awriter as aw

C_GREY = "#7e8e91"
C_WHITE = "#f8f8f2"
C_RED = "#f92672"
C_GREEN = "#a6e22e"

SYMB_MEMORY = "\uf1c0"
SYMB_CPU = "\uf108"
SYMB_SOUND_ON = "\uf028"
SYMB_SOUND_OFF = "\uf026"

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

def get_sound_pulseaudio():
    """
    Get sound from Pulseaudio.
    """

    try:
        sinks = sub.check_output(["pacmd", "list-sinks"])
    except sub.CalledProcessError:
        sinks = None

    if sinks is None:
        return [{
            "name": "volume",
            "instance": "pulseaudio",
            "full_text": "{}: ??%".format(SYMB_SOUND_ON),
            "color": C_RED
        }]

    sinks = sinks.strip()
    sinks = sinks.split("\n")
    sinks = [s.strip() for s in sinks]

    idx = [i for i, s in enumerate(sinks) if s.startswith("* index:")]
    idx = idx[0]
    sinks = sinks[idx:idx + 15]

    mute = [s for s in sinks if s.startswith("muted:")][0]
    mute = mute.split()[1]
    mute = (mute == "yes")

    vol = [s for s in sinks if s.startswith("volume:")][0]
    vol = vol.split()[4].strip("%")
    vol = int(vol)

    if mute or vol < 1:
        symb = SYMB_SOUND_OFF
        color = C_GREY
    else:
        symb = SYMB_SOUND_ON
        color = C_WHITE

    return [{
        "name": "volume",
        "instance": "pulseaudio",
        "full_text": "{}: {}%".format(symb, vol),
        "color": color
    }]

def get_cpuusage():
    """
    Get the cpu usage.
    """

    usages = psutil.cpu_percent(None, True)

    objs = []
    for i, usage in enumerate(usages, 1):
        usage = min(99.0, usage)

        objs.append({
            "name": "cpu_usage",
            "instance": i,
            "full_text": "{} {} {:2.0f}%".format(SYMB_CPU, i, usage),
            "color":  C_RED if usage >= 80 else C_GREEN
        })

    return objs

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

def main():
    uid = int(os.environ["UID"])
    extdir = "/run/user/{}/pbapps/i3status/external".format(uid)

    pidfile = extdir + "/90sys-state.pid"
    blockfile = extdir + "/90sys-state.block"

    with aw.open(pidfile, "w") as fobj:
        fobj.write(str(os.getpid()))

    while True:
        blocks = []

        blocks.extend(get_memusage())
        blocks.extend(get_cpuusage())
        blocks.extend(get_date())
        blocks.extend(get_sound_pulseaudio())

        with aw.open(blockfile, "w") as fobj:
            json.dump(blocks, fobj)

        time.sleep(1)

if __name__ == '__main__':
    main()
