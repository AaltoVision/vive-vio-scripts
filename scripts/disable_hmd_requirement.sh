#!/bin/sh
STEAM_VRSETTINGS="$1"
STEAM_NULL_DRIVER_VRSETTINGS="$2"
if [ ! -f "$STEAM_VRSETTINGS" ]; then
    echo "$STEAM_VRSETTINGS" is not a file!
    exit 1
fi
if [ ! -f "$STEAM_NULL_DRIVER_VRSETTINGS" ]; then
    echo "$STEAM_VRSETTINGS" is not a file!
    exit 1
fi
echo "Editing $STEAM_VRSETTINGS and $STEAM_NULL_DRIVER_VRSETTINGS"

# make backups if they do not exist
mkdir -p backups
if [ ! -f backups/steam_vrsettings ]; then
    echo "Backing up $STEAM_VRSETTINGS"
    cp "$STEAM_VRSETTINGS" backups/steam_vrsettings
fi
if [ ! -f backups/steam_null_driver_vrsettings ]; then
    echo "Backing up $STEAM_NULL_DRIVER_VRSETTINGS"
    cp "$STEAM_NULL_DRIVER_VRSETTINGS" backups/steam_null_driver_vrsettings 
fi

# settings
sed -i 's/\"requireHmd\": true/\"requireHmd\": false/g' "$STEAM_VRSETTINGS"
sed -i 's/\"forcedDriver\": ""/\"forcedDriver\": "null"/g' "$STEAM_VRSETTINGS" 
sed -i 's/\"activateMultipleDrivers\": false/\"activateMultipleDrivers\": true/g' "$STEAM_VRSETTINGS" 

# enable null driver
sed -i 's/\"enable\": false/\"enable\": true/g' "$STEAM_NULL_DRIVER_VRSETTINGS"
