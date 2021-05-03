#!/bin/sh

# Call this script with input file and output file as arguments
# e.g. ./preprocess-vio-data.sh input.jsonl output.jsonl
# Note: this still leaves the poses in the VIO-convention M = (R | -R_inverse*t)

if [ ! -f "$1" ]; then
    echo "$1 is not a file"
    exit 1
fi
# touch "$2" && grep -ir arcore "$1" > "$2"
touch "$2" && jq -c 'select(has("arcore")) | { time: .time, position: .arcore.position, orientation: .arcore.orientation }' < "$1" > "$2"
