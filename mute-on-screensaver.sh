#!/bin/bash

srcdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$srcdir/clean_bash.sh"
if [[ -r "$srcdir/venv/bin/activate" ]] ; then
    source "$srcdir/venv/bin/activate"
fi

export UID
exec python mute-on-screensaver.py
