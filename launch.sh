#!/bin/sh

pushd $(dirname `which $0`)
python3 src/main.py $*
popd
