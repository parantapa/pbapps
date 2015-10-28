#!/usr/bin/env python2
# encoding: utf-8
"""
Donwload image from Reddit for wallpapers.
"""

from __future__ import division, print_function, unicode_literals

__author__ = "Parantapa Bhattachara <pb [at] parantapa [dot] net>"

import os
import sys
import time
import json
import codecs
import random
import hashlib
from os.path import join, isdir, isfile
import signal
from ConfigParser import ConfigParser
from subprocess import call, check_output, CalledProcessError
from pipes import quote as shell_quote

import requests
import yaml
import logbook
from pypb import abspath
import pypb.awriter as aw

IMAGE_EXTS = "jpg JPG jpeg JPEG png PNG".split()

SYMB_REDDIT = "\uf1a1"
SYMB_SLEEPING = "\uf236"
SYMB_GET_IMG_LIST = "\uf021"
SYMB_DOWNLOAD_IMG = "\uf019"

def _dummy_handler(_, __): # pylint: disable=unused-argument
    """
    Pass; do nothing
    """

def _term_handler(signum, _):
    """
    Raise SystemExit.
    """

    raise SystemExit("Received Signal {} !".format(signum))

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

    block = {
        "full_text": "{}: {}".format(SYMB_REDDIT, text),
        "color": "#66d9ef"
    }

    with aw.copen(fname, "w", "utf-8") as fobj:
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

    cmd = "file %s" % shell_quote(fname)
    try:
        out = check_output(cmd, shell=True)
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

    posts = posts.json()["data"]["children"]
    posts = filter(_not_over_18, posts)
    urls  = map(_getimg, posts)
    urls  = map(_transform_imgur, urls)
    urls  = filter(_is_image_url, urls)

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

def set_nitrogen_bg(cfname, screen, fname, mode="auto", bgcolor=None):
    """
    Set the nitrogen background image.

    cfname  - Location for nitrogen's configuration
    screen  - Where to set the wall paper: fullscreen, screen1, screen2
    fname   - Image fname to use as background image
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
    conf.set(screen, "file", fname)
    conf.set(screen, "mode", mode)
    if bgcolor is not None:
        conf.set(screen, "bgcolor", bgcolor)

    # Write back config
    with open(cfname, "w") as fobj:
        conf.write(fobj)

    # Call nitrogen restore to update
    call("nitrogen --restore", shell=True)

def set_background(screen, mode, cfg):
    """
    Try to set the desktop background.
    """

    # Location of the state file
    log.info("Getting image list ...")
    state_update(SYMB_GET_IMG_LIST, cfg["statefile"])
    urls = []
    for sub in cfg["wallpaper-subs"]:
        us = get_subreddit_images(sub, cfg["user-agent"])
        urls.extend(us)
    urls = set(urls)

    # Load seen urls file
    log.info("Checking which urls have already been seen ...")
    if isfile(cfg["seen-urls-file"]):
        with open(cfg["seen-urls-file"]) as fobj:
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
        fname = join(cfg["savedir"], fname)

        # Download the image
        state_update(SYMB_DOWNLOAD_IMG, cfg["statefile"])
        if not download_image(url, fname):
            continue
        if not _is_image_file(fname):
            continue

        # Set background
        set_nitrogen_bg(cfg["nitrogen-bg-conf"], screen, fname, mode)
        break

    # Dump updated seen urls
    log.info("Writing down list of checked urls ...")
    with aw.open(cfg["seen-urls-file"], "w") as fobj:
        json.dump(sorted(seen_urls), fobj)

FNAME_KEYS = [
    "nitrogen-bg-conf",
    "savedir",
    "seen-urls-file",
    "pidfile",
    "statefile",
    "logfile"
]

def main():
    try:
        _, cfname = sys.argv # pylint: disable=unbalanced-tuple-unpacking
    except ValueError:
        print("Usage: ./reddit-bg.py <config.yaml>")
        sys.exit(0)

    cfname = abspath(cfname)

    # Load config
    with open(cfname, "r") as fobj:
        cfg = yaml.load(fobj)
    for key in FNAME_KEYS:
        cfg[key] = abspath(cfg[key])

    # Create the savedir if not exists
    if not isdir(cfg["savedir"]):
        log.info("Creating image saving directory {} ...", cfg["savedir"])
        os.makedirs(cfg["savedir"], 0o700)

    # Write pid to pidfile
    pid = str(os.getpid())
    log.info("Writing pid ({}) to {} ...", pid, cfg["pidfile"])
    with aw.open(cfg["pidfile"], "w") as fobj:
        fobj.write(pid)

    # Redirect stdout
    log.info("Redecting output to {} ...", cfg["logfile"])
    loghdl = logbook.FileHandler(cfg["logfile"])
    loghdl.push_application()

    # Setup the signal handlers
    signal.signal(signal.SIGUSR1, _dummy_handler)
    signal.signal(signal.SIGUSR2, _term_handler)
    signal.signal(signal.SIGTERM, _term_handler)
    signal.signal(signal.SIGINT, _term_handler)
    signal.signal(signal.SIGQUIT, _term_handler)

    while True:
        # Reload config
        with open(cfname, "r") as fobj:
            cfg = yaml.load(fobj)
        for key in FNAME_KEYS:
            cfg[key] = abspath(cfg[key])

        # Try to get set background
        for screen, mode in cfg["screens"]:
            set_background(screen, mode, cfg)

        # Go to sleep
        log.info("Next update after {} minutes.", cfg["update-interval"])
        state_update(SYMB_SLEEPING, cfg["statefile"])
        time.sleep(cfg["update-interval"] * 60)

if __name__ == '__main__':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    log = logbook.Logger("reddit-bg")
    logbook.StderrHandler().push_application()
    with log.catch_exceptions():
        main()
