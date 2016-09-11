# encoding: utf-8
"""
Common code required by most app scripts.
"""

import os
from os.path import join, dirname, abspath
import json
import signal
from subprocess import Popen, PIPE

import logbook
import pypb.awriter as aw
from pypb import register_exit_signals

PING_FILE = join(dirname(abspath(__file__)), "ping.wav")

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

ICONS = AttrDict({
    "fa_coffee": u"\uf0f4",
    "fa_graduation_cap": u"\uf19d",
    "fa_bed": u"\uf236",
    "fa_hdd_o": u"\uf0a0",
    "fa_floppy_o": u"\uf0c7",
    "fa_scissors": u"\uf0c4",
    "fa_spinner": u"\uf110",
    "fa_clock_o": u"\uf017",
    "fa_volume_off": u"\uf026",
    "fa_volume_up": u"\uf028",
    "fa_times": u"\uf00d",
    "fa_reddit": u"\uf1a1",
    "fa_refresh": u"\uf021",
    "fa_download": u"\uf019",
    "fa_warn": u"\uf071",
    "fa_memory": u"\uf1c0",
    "fa_cpu": u"\uf108",
})

COLORS = AttrDict({
    "red"     : "#f92672",
    "green"   : "#a6e22e",
    "orange"  : "#fd971f",
    "yellow"  : "#e6db74",
    "blue"    : "#66d9ef",
    "magenta" : "#ae81ff",
    "cyan"    : "#ae81ff",
    "white"   : "#f8f8f2",
    "grey"    : "#d2d2cd",
    "black"   : "#1b1d1e",
})

def _get_system_dir(fmt):
    """
    Get the system directory.
    """

    uid = os.environ["UID"]
    uid = int(uid)
    sysdir = fmt.format(uid)

    if not os.path.exists(sysdir):
        try:
            os.makedirs(sysdir, 0o700)
        except OSError:
            pass

    return sysdir

def get_i3status_rundir():
    """
    Get the directory for i3status to find .pid and .block files.
    """

    return _get_system_dir("/run/user/{}/pbapps/i3status/external")

def get_rundir():
    """
    Get the directory for regular .pid files.
    """

    return _get_system_dir("/run/user/{}/pbapps/run")

def get_logdir():
    """
    Get the directory for log files.
    """

    return _get_system_dir("/var/tmp/pbapps/log")

def wake_i3status():
    """
    Wake up the i3status program.
    """

    pidfile = get_rundir() + "/i3status.pid"
    try:
        # Get the pid
        with open(pidfile, "r") as fobj:
            pid = fobj.read().strip()
        pid = int(pid)

        # Send SIGUSR1
        os.kill(pid, signal.SIGUSR1)
    except (OSError, IOError, ValueError):
        pass

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


def fmt_period(period):
    """
    Format given period in seconds to string.
    """

    period = int(period)

    mm, ss = divmod(period, 60)
    hh, mm = divmod(mm, 60)
    dd, hh = divmod(hh, 24)

    if dd:
        fmt = "{} day{}, {}:{:02d}:{:02d}".format
        return fmt(dd, ("s" if dd > 1 else ""), hh, mm, ss)
    elif hh:
        fmt = "{}:{:02d}:{:02d}".format
        return fmt(hh, mm, ss)
    elif mm:
        fmt = "{}:{:02d}".format
        return fmt(mm, ss)
    else:
        return "{}s".format(ss)

def sound_ping():
    """
    Make pinging sound.
    """

    cmd = ["aplay", PING_FILE]
    Popen(cmd).wait()

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


def dummy_handler(signum, frame): # pylint: disable=unused-argument
    """
    Pass; do nothing
    """

def do_main(modname, prio, iterable):
    """
    Run the main function.
    """

    # Setup logfile
    logfile = "%s/%s.log" % (get_logdir(), modname)
    logbook.FileHandler(logfile).push_application()

    log = logbook.Logger(modname)

    with log.catch_exceptions():
        # Get the external state directory
        extdir = get_i3status_rundir()

        # Write out my own pid
        pidfile = "%s/%d%s.pid" % (extdir, prio, modname)
        with open(pidfile, "w") as fobj:
            fobj.write(str(os.getpid()))

        register_exit_signals()

        # File to write block info
        blockfile = "%s/%d%s.block" % (extdir, prio, modname)

        while True:
            for blocks in iterable:
                with aw.open(blockfile, "w") as fobj:
                    json.dump(blocks, fobj)
                wake_i3status()
