#!/usr/bin/env python2
# encoding: utf-8
"""
Simple alarm app.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
from os.path import join, dirname, abspath
import time
import json
from subprocess import Popen, PIPE

import arrow

import pypb.awriter as aw
from pypb.dmn_misc import dmn_pid
from pbapps_common import get_i3status_rundir, wake_i3status

C_WHITE = "#f8f8f2"

SYMB_CLOCK = "\uf017"

PING_FILE = join(dirname(abspath(__file__)), "ping.wav")

def sound_ping():
    """
    Make pinging sound.
    """

    cmd = ["aplay", PING_FILE]
    Popen(cmd).wait()

def parse_period(text):
    """
    Parse the time period

    Returns the number of seconds.
    """

    text = text.strip()
    if not text:
        raise ValueError("Time period text empty")

    # Normal integer means, time period in minutes.
    if text.isdigit():
        return int(text) * 60

    period = 0
    parts = text.split()
    for part in parts:
        if len(part) < 2:
            raise ValueError("Invalid time period: '%s'" % text)

        head, tail = part[:-1], part[-1]
        if not head.isdigit() or tail not in "hHmMsSdD":
            raise ValueError("Invalid time period: '%s'" % text)

        multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[tail.lower()]
        period += int(head) * multiplier

    return period

def show_entry_dialog(title, dialog_text, entry_text_default):
    """
    Get a text entered by the user.
    """

    cmd = ["zenity", "--entry",
           "--title=%s" % title,
           "--text=%s" % dialog_text,
           "--entry-text=%s" % entry_text_default]
    proc = Popen(cmd, stdout=PIPE)
    stdout, _ = proc.communicate()
    stdout = stdout.strip()

    return stdout.decode("utf-8")

def show_notificaiton(urgency, expire_time, summary, body):
    """
    Disply notification.
    """

    cmd = ["notify-send",
           "--urgency=%s" % urgency,
           "--expire-time=%s" % (expire_time * 1000),
           summary,
           body]
    Popen(cmd).wait()

def normalize_name(text):
    return "".join(c for c in text.lower() if c.isalnum())

def fmt_period(period):
    """
    Format given period in seconds to string.
    """

    mm, ss = divmod(period, 60)
    hh, mm = divmod(mm, 60)
    dd, hh = divmod(hh, 24)

    if dd:
        fmt = "{} day{}, {}:{:02d}:{:02d}".format
        return fmt(dd, (dd, "s" if dd > 1 else ""), hh, mm, ss)
    elif hh:
        fmt = "{}:{:02d}:{:02d}".format
        return fmt(hh, mm, ss)
    elif mm:
        fmt = "{}:{:02d}".format
        return fmt(mm, ss)
    else:
        return "{}s".format(ss)

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
    now = arrow.now().timestamp
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
        now = arrow.now().timestamp

    show_notificaiton("critical", 0, "Time up", "%s finished" % name)
    sound_ping()

if __name__ == '__main__':
    main()
