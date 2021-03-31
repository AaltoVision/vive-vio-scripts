#!/bin/sh

# Path to the vrsettings file to edit, for example
# "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\resources\settings\default.vrsettings"
STEAM_VRSETTINGS="$1"

# Path to the "null" driver vrsettings file to edit, for example
# "C:\Program Files (x86)\Steam\steamapps\common\SteamVR\drivers\null\resources\settings\default.vrsettings"
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

# Make backups if they do not exist yet
mkdir -p backups
if [ ! -f backups/steam_vrsettings ]; then
    echo "Backing up $STEAM_VRSETTINGS to ./backups/steam_vrsettings"
    cp "$STEAM_VRSETTINGS" backups/steam_vrsettings
fi
if [ ! -f backups/steam_null_driver_vrsettings ]; then
    echo "Backing up $STEAM_NULL_DRIVER_VRSETTINGS to ./backups/steam_null_driver_vrsettings"
    cp "$STEAM_NULL_DRIVER_VRSETTINGS" backups/steam_null_driver_vrsettings 
fi

# Override the settings to make HMD not required for recording tracker data
sed -i 's/\"requireHmd\": true/\"requireHmd\": false/g' "$STEAM_VRSETTINGS"
sed -i 's/\"forcedDriver\": ""/\"forcedDriver\": "null"/g' "$STEAM_VRSETTINGS" 
sed -i 's/\"activateMultipleDrivers\": false/\"activateMultipleDrivers\": true/g' "$STEAM_VRSETTINGS" 
sed -i 's/\"enable\": false/\"enable\": true/g' "$STEAM_NULL_DRIVER_VRSETTINGS"
