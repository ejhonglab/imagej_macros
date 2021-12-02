#!/usr/bin/env bash

FIJI_PATH=$HOME/Fiji.app

if ! [ -d "$FIJI_PATH" ]; then
    >&2 echo "FIJI_PATH=${FIJI_PATH} did not exist"
    exit 1
fi

# Directory containing this script
# https://stackoverflow.com/questions/59895
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ln -sv ${SCRIPT_DIR}/*.py $FIJI_PATH/plugins

# TODO update section at end of $FIJI_PATH/macros/StartupMacros.fiji.ijm automatically
# with contents of $SCRIPT_DIR/startup_macros.fiji.ijm
#local indicator_line
#if grep -qxF "$"

# TODO also set (via xdg-mime?) imagej to be the default application to open tiffs

