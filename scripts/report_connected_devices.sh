#!/bin/sh
cmake --build build --target ovr-report-connected-devices --config RelWithDebInfo > /dev/null
build/RelWithDebInfo/ovr-report-connected-devices.exe
