#!/usr/bin/env bash

FIJI_DIR=$HOME/Fiji.app

if ! [ -d "${FIJI_DIR}" ]; then
    >&2 echo "FIJI_DIR=${FIJI_DIR} did not exist"
    exit 1
fi

# Directory containing this script
# https://stackoverflow.com/questions/59895
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ln -sv ${SCRIPT_DIR}/*.py ${FIJI_DIR}/plugins

MACRO_DIR=${FIJI_DIR}/macros
# The former installs the macros in the latter when Fiji starts.
ln -sv ${SCRIPT_DIR}/install_macros.ijm ${MACRO_DIR}/AutoRun/install_macros.ijm
# This file contains most of my hotkey definitions (some others are internal to some of
# the Jython scripts). Note that we are giving the link for this one a different name.
ln -sv ${SCRIPT_DIR}/startup_macros.ijm ${MACRO_DIR}/toolsets/hong.ijm

# TODO also set (via xdg-mime?) imagej to be the default application to open tiffs

