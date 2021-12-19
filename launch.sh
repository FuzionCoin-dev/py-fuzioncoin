#!/bin/sh

START_DIR=$(pwd)
cd $(dirname `which $0`)
python3 src/main.py $*
cd $START_DIR
