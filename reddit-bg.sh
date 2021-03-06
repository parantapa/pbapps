#!/bin/bash

srcdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$srcdir/clean_bash.sh"
if [[ -r "$srcdir/venv/bin/activate" ]] ; then
    source "$srcdir/venv/bin/activate"
fi

source "$HOME/.bashrc"
export UID

exec python "${srcdir}/reddit-bg.py" "${srcdir}/reddit-bg.conf.yaml"
