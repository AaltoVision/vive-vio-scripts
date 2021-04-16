#!/bin/sh

echo "Datasets on device:"
adb shell ls "storage/emulated/0/Android/data/org.example.viotester/cache/recordings"

echo "Downloading all datasets"
adb pull "storage/emulated/0/Android/data/org.example.viotester/cache/recordings/" data/viotester/
