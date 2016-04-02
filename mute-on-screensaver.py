#!/usr/bin/env python2
# encoding: utf-8
"""
Watch xscreensaver and turn off volume when on.
"""

from __future__ import print_function, unicode_literals

import os
import json
from subprocess import Popen, PIPE, STDOUT

import logbook

import pypb.awriter as aw
from pypb import register_exit_signals
from pbapps_common import get_i3status_rundir, \
                          get_logdir

SYMB_MUTE_ON_SCREENSAVER = "\uf026 \uf00d"
C_ORANGE = "#fd971f"

MODULE = "mute-on-screensaver"

def do_main():
    """
    Observe the screensaver.
    """

    cmd = ["xscreensaver-command", "-watch"]
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT)

    # NOTE: As of today (July 20, 2015) we can't use
    # ``for line in proc.stdout'' here because of the following bug
    # http://bugs.python.org/issue3907
    for line in iter(proc.stdout.readline, ""):
        line = line.strip()

        if line.startswith("BLANK") or line.startswith("LOCK"):
            cmd = ["sound-ctrl", "mute"]
            Popen(cmd).wait()

def main():
    prio = 20

    # Setup logfile
    logfile = "%s/%s.log" % (get_logdir(), MODULE)
    logbook.FileHandler(logfile).push_application()

    log = logbook.Logger(MODULE)

    with log.catch_exceptions():
        # Get the external state directory
        extdir = get_i3status_rundir()

        # Write out my own pid
        pidfile = "%s/%d%s.pid" % (extdir, prio, MODULE)
        with open(pidfile, "w") as fobj:
            fobj.write(str(os.getpid()))

        register_exit_signals()

        # File to write block info
        blockfile = "%s/%d%s.block" % (extdir, prio, MODULE)

        with aw.open(blockfile, "w") as fobj:
            fobj.write(json.dumps({
                "name": "mute_on_screensaver",
                "full_text": SYMB_MUTE_ON_SCREENSAVER,
                "color": C_ORANGE
            }))

        do_main()

if __name__ == '__main__':
    main()
