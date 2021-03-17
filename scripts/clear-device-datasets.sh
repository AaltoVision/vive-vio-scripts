#!/bin/sh
echo "Removing all datasets from device"
adb shell 'rm -r /storage/emulated/0/Android/data/org.example.viotester/cache/recordings/*'
