#!/usr/bin/env python2
# encoding: utf-8
"""
Watch xscreensaver and turn off volume when on.
"""

from __future__ import print_function, unicode_literals

import os
import json
from subprocess import Popen, PIPE, STDOUT

import pypb.awriter as aw

SYMB_MUTE_ON_SCREENSAVER = "\uf1b3"
C_GREEN = "#fd971f"

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
    uid = int(os.environ["UID"])
    extdir = "/run/user/{}/pbapps/i3status/external".format(uid)

    pidfile = extdir + "/20mute-on-screenaver.pid"
    blockfile = extdir + "/20mute-on-screenaver.block"

    with aw.open(pidfile, "w") as fobj:
        fobj.write(str(os.getpid()))

    with aw.open(blockfile, "w") as fobj:
        fobj.write(json.dumps({
            "name": "mute_on_screensaver",
            "full_text": SYMB_MUTE_ON_SCREENSAVER,
            "color": C_GREEN
        }))

    do_main()

if __name__ == '__main__':
    main()
