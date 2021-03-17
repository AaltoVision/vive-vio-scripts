#!/bin/sh

# Call this script with input file and output file as arguments
# e.g. ./preprocess-vio-data.sh input.jsonl output.jsonl

if [ ! -f "$1" ]; then
    echo "$1 is not a file"
    exit 1
fi
# touch "$2" && grep -ir arcore "$1" > "$2"
touch "$2" && jq -c 'select(has("arcore")) | { position: .arcore.position, time: .time }' < "$1" > "$2"
