#!/bin/bash

srcdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$srcdir/clean_bash.sh"
if [[ -r "$srcdir/venv/bin/activate" ]] ; then
    source "$srcdir/venv/bin/activate"
fi

source "$HOME/.bashrc"

script="$1"

export UID
exec python "${srcdir}/${script}.py"
