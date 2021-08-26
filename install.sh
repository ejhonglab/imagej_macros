#!/usr/bin/env bash

FIJI_PATH=$HOME/Fiji.app

if ! [ -d "$FIJI_PATH" ]; then
    >&2 echo "FIJI_PATH=${FIJI_PATH} did not exist"
    exit 1
fi

# https://stackoverflow.com/questions/59895
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

ln -sv ${SCRIPT_DIR}/*.py $FIJI_PATH/plugins

#local indicator_line
#if grep -qxF "$"
