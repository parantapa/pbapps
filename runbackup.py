#!/usr/bin/env python2
# encoding: utf-8
"""
Run borg backup.
"""

from __future__ import division, print_function, unicode_literals

import time
import socket
import signal
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT

import logbook

from pbapps_common import do_main, dummy_handler, ICONS, COLORS

MODULE = "runbackup"

REPOSITORY = "/run/media/parantapa/backup1/ra_backup/workspace.borg"
SRC_DIRS = [
    "/home/parantapa/workspace",
    "/home/parantapa/drafts"
]
SLEEP_TIME = 15

log = logbook.Logger(MODULE)

def backup_iter():
    """
    Run actual backup code.
    """

    hostname = socket.gethostname()

    log.info("Sleeping for {} mins ...", SLEEP_TIME)
    yield [{"name": MODULE, "full_text": ICONS.fa_bed, "color": COLORS.green}]
    time.sleep(SLEEP_TIME * 60)

    while True:
        list_cmd = ["borg", "list", REPOSITORY]
        log.info("Check borg repo:\n{}", str(list_cmd))
        yield [{"name": MODULE, "full_text": ICONS.fa_spinner, "color": COLORS.white}]
        proc = Popen(list_cmd, stdout=PIPE, stderr=STDOUT)
        stdout, _ = proc.communicate()
        retcode = proc.returncode
        log.info("List repos completed with: {}\n{}", retcode, stdout)

        if retcode != 0:
            log.warn("Falied to confirm repo state")
            log.info("Sleeping for 1 min ...")
            yield [{"name": MODULE, "full_text": ICONS.fa_hdd_o, "color": COLORS.red}]
            time.sleep(60)
            continue

        timestamp = datetime.now()
        timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        archive = "%s::%s-%s" % (REPOSITORY, hostname, timestamp)

        backup_cmd = ["borg", "create",
                      "--verbose", "--stats",
                      "--compression", "lz4",
                      archive]
        backup_cmd += SRC_DIRS

        log.info("Running backup command:\n{}", str(backup_cmd))
        yield [{"name": MODULE, "full_text": ICONS.fa_hdd_o, "color": COLORS.cyan}]
        time.sleep(10)
        proc = Popen(backup_cmd, stdout=PIPE, stderr=STDOUT)
        stdout, _ = proc.communicate()
        retcode = proc.returncode
        log.info("Backup completed with: {}\n{}", retcode, stdout)

        prune_cmd = ["borg", "prune",
                     "--verbose",
                     "--prefix", ("%s-" % hostname),
                     "--keep-within", "7d",
                     "--keep-weekly", "5",
                     "--keep-monthly", "12",
                     REPOSITORY]

        log.info("Running prune command:\n{}", str(prune_cmd))
        yield [{"name": MODULE, "full_text": ICONS.fa_scissors, "color": COLORS.cyan}]
        time.sleep(10)
        proc = Popen(prune_cmd, stdout=PIPE, stderr=STDOUT)
        stdout, _ = proc.communicate()
        retcode = proc.returncode
        log.info("Backup completed with: {}\n{}", retcode, stdout)

        log.info("Sleeping for {} mins ...", SLEEP_TIME)
        yield [{"name": MODULE, "full_text": ICONS.fa_bed, "color": COLORS.green}]
        time.sleep(SLEEP_TIME * 60)

def main():
    signal.signal(signal.SIGUSR1, dummy_handler)

    do_main(MODULE, 60, backup_iter())

if __name__ == '__main__':
    main()
