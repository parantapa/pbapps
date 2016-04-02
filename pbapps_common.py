# encoding: utf-8
"""
Common code required by most app scripts.
"""

import os
import json

import logbook
import pypb.awriter as aw
from pypb import register_exit_signals

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
