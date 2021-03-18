#!/bin/sh
cmake --build build --target ovr-tracker-app --config RelWithDebInfo > /dev/null
build/RelWithDebInfo/ovr-tracker-app.exe
