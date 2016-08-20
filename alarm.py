#!/usr/bin/env python2
# encoding: utf-8
"""
Simple alarm app.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
import time
import json

import pypb.awriter as aw
from pypb.dmn_misc import dmn_pid
from pbapps_common import get_i3status_rundir, wake_i3status, \
                          parse_period, fmt_period, sound_ping,\
                          show_notificaiton, show_entry_dialog \

C_WHITE = "#f8f8f2"

SYMB_CLOCK = "\uf017"

def normalize_name(text):
    return "".join(c for c in text.lower() if c.isalnum())

def main():
    # Create the external state directory
    extdir = get_i3status_rundir()

    # Get alarm time
    period = show_entry_dialog("Alarm", "Enter time period", "25m")
    try:
        period = parse_period(period)
    except ValueError as e:
        show_notificaiton("normal", 5, "Alarm set error", str(e))
        return

    # Get alarm name
    name = show_entry_dialog("Alarm", "Enter alarm name", "Pomodoro")
    cname = normalize_name(name)

    # Get the alarm name
    pidfile = extdir + ("/30alarm-%s.pid" % cname)
    blockfile = extdir + ("/30alarm-%s.block" % cname)
    pid = dmn_pid(pidfile)
    if pid is not None:
        show_notificaiton("normal", 5, "Alarm set error",
                          "Alarm with same name already running")
        return

    # Write out the pid
    with aw.open(pidfile, "w") as fobj:
        fobj.write(str(os.getpid()))

    # Start the loop
    now = time.time()
    end = now + period
    while now < end:
        full_text = "{} {}: {}".format
        full_text = full_text(SYMB_CLOCK, name, fmt_period(end - now))

        with aw.open(blockfile, "w") as fobj:
            fobj.write(json.dumps({
                "name": "cname",
                "full_text": full_text,
                "color": C_WHITE
            }))
        wake_i3status()

        time.sleep(2)
        now = time.time()

    show_notificaiton("critical", 0, "Time up", "%s finished" % name)
    sound_ping()

if __name__ == '__main__':
    main()
