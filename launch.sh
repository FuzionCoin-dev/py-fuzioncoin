#!/bin/sh

LAUNCH_PATH=$(pwd)
pushd $(dirname `which $0`)
python3 src/main.py --launch-path $LAUNCH_PATH $*
popd
