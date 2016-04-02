#!/usr/bin/env python2
# encoding: utf-8
"""
Display state of pulseauio.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
import subprocess as sub

from pbapps_common import do_main

MODULE = "pulseaudio-state"

C_GREY = "#7e8e91"
C_WHITE = "#f8f8f2"
C_RED = "#f92672"

SYMB_SOUND_ON = "\uf028"
SYMB_SOUND_OFF = "\uf026"

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

def blocks_iter():
    while True:
        yield get_sound_pulseaudio()
        time.sleep(1)

def main():
    do_main(MODULE, 95, blocks_iter())

if __name__ == '__main__':
    main()
