#!/bin/sh
awk -v rate="$1" 'NR % rate == 0' "$2"
