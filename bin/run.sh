#!/bin/sh

CURRENT_DIR=`pwd`

kill -9 `ps -ef | grep "python.*src/collect.py" | grep -v grep | awk '{print $2}'`

python $CURRENT_DIR/../src/collect.py

