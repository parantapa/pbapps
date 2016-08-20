#!/usr/bin/env python2
# encoding: utf-8
"""
Keep circle for study play mode switch.

Keeps a personal log of work-vs play modes
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import time
import signal
import json

import logbook

from pbapps_common import do_main, fmt_period, \
                          show_entry_dialog, \
                          ICONS, COLORS

MODULE = "study-play-mode"

STUDY_ICON = ICONS.fa_graduation_cap
PLAY_ICON = ICONS.fa_coffee

CUR_MODE = "play"
CUR_MODE_START = time.time()

log = logbook.Logger(MODULE)

def switch_mode(signum, frame): # pylint: disable=unused-argument
    """
    Swith the mode and reset mode start time.
    """

    global CUR_MODE, CUR_MODE_START

    last_mode = CUR_MODE
    last_mode_start = CUR_MODE_START

    if CUR_MODE == "play":
        CUR_MODE = "study"
    else:
        CUR_MODE = "play"

    CUR_MODE_START = time.time()

    if last_mode == "study":
        title = "Notes"
        dialog_text = "What did you do last session?"
        entry_text_default = "?"
        notes = show_entry_dialog(title, dialog_text, entry_text_default)
    else:
        notes = None

    mode_log = {
        "mode": last_mode,
        "mode_start": last_mode_start,
        "mode_end": CUR_MODE_START,
        "notes": notes
    }
    mode_log = json.dumps(mode_log)
    log.info("switched-mode {}", mode_log)

def blocks_iter():
    """
    Yield the blocks to send to i3status.
    """

    while True:
        if CUR_MODE == "play":
            icon = PLAY_ICON
            color = COLORS.orange
        else:
            icon = STUDY_ICON
            color = COLORS.magenta

        runtime = time.time() - CUR_MODE_START
        runtime = fmt_period(runtime)

        yield [{"name": MODULE,
                "full_text": "%s: %s" % (icon, runtime),
                "color": color}]
        time.sleep(2)

def main():
    signal.signal(signal.SIGUSR1, switch_mode)

    do_main(MODULE, 20, blocks_iter())

if __name__ == '__main__':
    main()
