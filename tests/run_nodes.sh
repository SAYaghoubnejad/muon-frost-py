#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <node-number>"
    exit 1
fi

rm -rf logs
mkdir logs

range=$(( $1 - 1 ))

for i in $(seq 0 "$range"); do
    python node/main.py $i &
done