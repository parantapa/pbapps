# Source this script for a clean bash environment with virtualenv.
#
# Add the following lines at the top of the bash script.
#
# srcdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# source "$srcdir/clean_bash.sh"
# if [[ -r "$srcdir/venv/bin/activate" ]] ; then
#     source "$srcdir/venv/bin/activate"
# fi
#
# NOTE: This script assumes it is being sourced from the main script.

# Start a clean version of bash
if [[ "$1" != "--norc" ]] || [[ "$2" != "--noprofile" ]] ; then
    exec /usr/bin/env -i \
        HOME="$HOME" \
        DISPLAY="$DISPLAY" \
        XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" \
        /bin/bash "${BASH_SOURCE[1]}" --norc --noprofile "$@"
fi

# Remove the --norc and --noprofile flags
shift 2

# Source /etc/profile
. /etc/profile

# We have guest specific setup code.
if [[ -r "$HOME/guest-clean_bash.sh" ]] ; then
    . "$HOME/guest-clean_bash.sh"
fi

# Check if we have vritualenv defined
hash virtualenv 2>/dev/null
if [[ $? -ne 0 ]] ; then
    echo "Couldn't find virtualenv."
    exit 1
fi
