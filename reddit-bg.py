#!/usr/bin/env python2
# encoding: utf-8
"""
Donwload image from Reddit for wallpapers.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
from os.path import join, isdir, isfile
import sys
import time
import json
import random
import signal
import hashlib
from ConfigParser import ConfigParser
from subprocess import call, check_output, CalledProcessError

import yaml
import logbook
import requests

from pypb import abspath
import pypb.awriter as aw
from pypb import register_exit_signals

from pbapps_common import get_i3status_rundir, \
                          get_logdir, \
                          dummy_handler

MODULE = "reddit-bg"

IMAGE_EXTS = "jpg JPG jpeg JPEG png PNG".split()

SYMB_REDDIT = "\uf1a1"
SYMB_SLEEPING = "\uf236"
SYMB_GET_IMG_LIST = "\uf021"
SYMB_DOWNLOAD_IMG = "\uf019"

log = logbook.Logger(MODULE)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

def _req_get(*args, **kwargs):
    """
    Do a requests.get in a try catch block to catch all exceptions;
    """

    kwargs.setdefault("timeout", 60)

    try:
        r = requests.get(*args, **kwargs)
        return r
    except Exception: # pylint: disable=broad-except
        log.warn("Received unknown exception", exc_info=True)
        return None

def state_update(text, fname):
    """
    Write text to file atomically. Text may contain unicode.
    """

    block = [{
        "full_text": "{}: {}".format(SYMB_REDDIT, text),
        "color": "#66d9ef"
    }]

    with aw.open(fname, "w") as fobj:
        json.dump(block, fobj)

def _not_over_18(post):
    """
    Chcek not NSFW.
    """

    return not post["data"]["over_18"]

def _getimg(post):
    """
    Return URL.
    """

    return post["data"]["url"]

def _transform_imgur(url):
    """
    Transform imgur urls.
    """

    for ext in IMAGE_EXTS:
        if url.endswith("." + ext):
            return url

    check = {
        "http://imgur.com/a/": False,
        "https://imgur.com/a/": False,
        "http://imgur.com": True,
        "https://imgur.com": True,
    }
    for prefix, code in check.items():
        if url.startswith(prefix):
            if code:
                return url + ".jpg"
            else:
                return url

    return url

def _is_image_url(url):
    """
    Check if url is image url.
    """

    for ext in IMAGE_EXTS:
        if url.endswith("." + ext):
            return True

    return False

def _getext(url):
    """
    From url get file extension.
    """

    for ext in IMAGE_EXTS:
        if url.endswith("." + ext):
            return ext

    return "jpg"

def _is_image_file(fname):
    """
    Check if given file is an image file.
    """

    if not isfile(fname):
        return False

    cmd = ["file", fname]
    try:
        out = check_output(cmd)
    except CalledProcessError:
        return False

    if "PNG image data" in out or "JPEG image data" in out:
        return True

    return False

def get_subreddit_images(subreddit, user_agent):
    """
    Get the images posted in a given subreddit.

    subreddit - url of the subreddit's json file
    user_agent - user agent strint to use for crawling reddit
    """

    headers = {"User-Agent": user_agent}
    params = {"limit": 100}

    log.info("Getting pics from /r/{} ...", subreddit)
    urlfmt = "http://www.reddit.com/r/{}/.json".format
    posts = _req_get(urlfmt(subreddit), headers=headers, params=params)
    if posts is None or posts.status_code != 200:
        log.warn("Getting pics from /r/{} failed!", subreddit)
        return []

    try:
        posts = posts.json()["data"]["children"]
        posts = filter(_not_over_18, posts)
        urls  = map(_getimg, posts)
        urls  = map(_transform_imgur, urls)
        urls  = filter(_is_image_url, urls)
    except (ValueError, KeyError):
        return []

    return list(urls)

def download_image(url, fname):
    """
    Download the image in url to the given file.
    """

    log.info("Downloading image from {} ...", url)
    resp = _req_get(url)

    if resp is not None and resp.status_code == 200:
        log.info("Saving to {} ...", fname)
        with open(fname, "wb") as fobj:
            fobj.write(resp.content)
        return True

    log.warn("Downloading failed!")
    return False

def set_nitrogen_bg(cfname, screen, ifname, mode="auto", bgcolor=None):
    """
    Set the nitrogen background image.

    cfname  - Location for nitrogen's configuration
    screen  - Where to set the wall paper: fullscreen, screen1, screen2
    ifname  - Image fname to use as background image
    mode    - scaled, auto, centered
    bgcolor - Background color for the desktop
    """

    log.info("Setting background image in nitrogen ...")

    # Setup the proper value of screen
    screen = {
        "fullscreen" : ":0.0",
        "screen1"    : "xin_0",
        "screen2"    : "xin_1"
    }[screen]

    # Setup poper value for mode
    mode = {
        "scaled"   : 0,
        "auto"     : 4,
        "centered" : 2
    }[mode]
    mode = str(mode)

    # Read the config
    conf = ConfigParser()
    conf.read(cfname)

    # Fix in the stuff to fill in
    conf.set(screen, "file", ifname)
    conf.set(screen, "mode", mode)
    if bgcolor is not None:
        conf.set(screen, "bgcolor", bgcolor)

    # Write back config
    with open(cfname, "w") as fobj:
        conf.write(fobj)

    # Call nitrogen restore to update
    call(["nitrogen", "--restore"])

def set_background(screen, mode, cfg, statefile):
    """
    Try to set the desktop background.
    """

    # Location of the state file
    log.info("Getting image list ...")
    state_update(SYMB_GET_IMG_LIST, statefile)
    urls = []
    for sub in cfg.wallpaper_subreddits:
        us = get_subreddit_images(sub, cfg.user_agent)
        urls.extend(us)
    urls = set(urls)

    # Load seen urls file
    log.info("Checking which urls have already been seen ...")
    if isfile(cfg.seenurls_fname):
        with open(cfg.seenurls_fname) as fobj:
            seen_urls = set(json.load(fobj))
    else:
        seen_urls = set()

    # Create unseen urls list
    unseen_urls = urls - seen_urls
    if not unseen_urls:
        unseen_urls = urls
    unseen_urls = list(unseen_urls)
    random.shuffle(unseen_urls)

    for url in unseen_urls:
        seen_urls.add(url)

        # Create a unique filename for the url
        uhash = hashlib.sha1(url.encode("utf-8")).hexdigest()
        fname = "%s.%s" % (uhash, _getext(url))
        fname = join(cfg.save_dir, fname)

        # Download the image
        state_update(SYMB_DOWNLOAD_IMG, statefile)
        if not download_image(url, fname):
            continue
        if not _is_image_file(fname):
            continue

        # Set background
        set_nitrogen_bg(cfg.nitrogen_conf_fname, screen, fname, mode)
        break

    # Dump updated seen urls
    log.info("Writing down list of checked urls ...")
    with aw.open(cfg.seenurls_fname, "w") as fobj:
        json.dump(sorted(seen_urls), fobj)

def read_cfg(fname):
    # pylint: disable=attribute-defined-outside-init,no-member
    """
    Read the config.
    """

    with open(fname, "r") as fobj:
        cfg = yaml.load(fobj)
    cfg = AttrDict(cfg)

    cfg.save_dir = abspath(cfg.save_dir)
    cfg.seenurls_fname = abspath(cfg.seenurls_fname)
    cfg.nitrogen_conf_fname = abspath(cfg.nitrogen_conf_fname)

    return cfg

def do_main(statefile):
    # pylint: disable=no-member
    """
    Run the actual code.
    """

    try:
        _, cfname = sys.argv # pylint: disable=unbalanced-tuple-unpacking
    except ValueError:
        print("Usage: ./reddit-bg.py <config.yaml>")
        sys.exit(1)
    cfname = abspath(cfname)

    # Load config
    cfg = read_cfg(cfname)

    # Create the savedir if not exists
    if not isdir(cfg.save_dir):
        log.info("Creating image saving directory {} ...", cfg.save_dir)
        os.makedirs(cfg.save_dir, 0o700)

    while True:
        # Reload config
        cfg = read_cfg(cfname)

        # Try to get set background
        for screen, mode in cfg.screens:
            set_background(screen, mode, cfg, statefile)

        # Go to sleep
        log.info("Next update after {} minutes.", cfg.update_interval)
        state_update(SYMB_SLEEPING, statefile)
        time.sleep(cfg.update_interval * 60)

def main():
    prio = 30

    # Setup logfile
    logfile = "%s/%s.log" % (get_logdir(), MODULE)
    logbook.FileHandler(logfile).push_application()

    with log.catch_exceptions():
        # Get the external state directory
        extdir = get_i3status_rundir()

        # Write out my own pid
        pidfile = "%s/%d%s.pid" % (extdir, prio, MODULE)
        with open(pidfile, "w") as fobj:
            fobj.write(str(os.getpid()))

        register_exit_signals()
        signal.signal(signal.SIGUSR1, dummy_handler)

        # File to write block info
        blockfile = "%s/%d%s.block" % (extdir, prio, MODULE)

        do_main(blockfile)

if __name__ == '__main__':
    main()
