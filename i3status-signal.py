#!/usr/bin/env python2
# encoding: utf-8
"""
Signal i3status block programs.
"""

from __future__ import division, print_function


__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
import signal
from subprocess import Popen, PIPE

import logbook

from i3status import get_pids
from pbapps_common import get_i3status_rundir, get_logdir

log = logbook.Logger("i3status-signal")

def do_main():
    """
    Send the signal to the process.
    """

    # Create the external state directory
    extdir = get_i3status_rundir()

    # Get the service pids
    service_pids = get_pids(extdir)

    # If we dont have any active services then exit
    if not service_pids:
        log.info("No active services found.")
        return

    # Select the service name
    cmd = ["dmenu-wrap"]
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    service, _ = proc.communicate("\n".join(sorted(service_pids)))
    service = service.strip()
    log.info("Selected service: {}", service)

    # Signal list
    signame_signum = {
        "usr1": signal.SIGUSR1,
        # "usr2": signal.SIGUSR2,
        # "kill": signal.SIGKILL,
        # "term": signal.SIGTERM,
        "-": None
    }

    # Select the signal to send
    cmd = ["dmenu-wrap"]
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    signame, _ = proc.communicate("\n".join(signame_signum))
    signame = signame.strip()
    log.info("Selected signam: {}", signal)

    # If we dont select any signal then exit.
    if signame == "-":
        log.info("Got empty signal ..")
        return

    # Send signal to code
    pid = service_pids[service]
    signum = signame_signum[signame]

    log.info("Sending signal {} to pid {} ...", signum, pid)
    os.kill(pid, signum)

def main():
    # Setup logfile
    logfile = get_logdir() + "/i3status-signal.log"
    logbook.FileHandler(logfile).push_application()

    with log.catch_exceptions():
        do_main()

if __name__ == '__main__':
    main()
