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

from i3status import get_pids

def main():
    # Create the external state directory
    uid = os.environ["UID"]
    uid = int(uid)
    extdir = "/run/user/{}/pbapps/i3status/external"
    extdir = extdir.format(uid)

    # Get the service pids
    service_pids = get_pids(extdir)

    # If we dont have any active services then exit
    if not service_pids:
        return

    # Select the service name
    cmd = ["dmenu-wrap"]
    proc = Popen(cmd, stdin=PIPE, stdout=PIPE)
    service, _ = proc.communicate("\n".join(service_pids))
    service = service.strip()

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

    # If we dont select any signal then exit.
    if signame == "-":
        return

    # Send signal to code
    pid = service_pids[service]
    signum = signame_signum[signame]
    os.kill(pid, signum)

if __name__ == '__main__':
    main()
