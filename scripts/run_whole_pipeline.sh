#!/bin/sh

# Just give path to the .jsonl(s) pulled from the device(s), and to the tracker data .jsonl file, and folder to work in, and this script will do all steps for aligning trajectories and time syncing
# NOTE: calibration (aligning trajectories) was not finished yet

[[ -z "$1" ]] && { echo "Parameter 1 (device data jsonl file) is missing" ; exit 1; }
[[ -z "$2" ]] && { echo "Parameter 2 (tracker data jsonl file) is missing" ; exit 1; }
[[ -z "$3" ]] && { echo "Parameter 3 (output dir) is missing" ; exit 1; }

DEVICE_DATA_JSONL_FILE="$1"
TRACKER_DATA_JSONL_FILE="$2"
OUTPUT_DIR="$3"

TRACKER_DOWNSAMPLE_RATE=1000

printf "Using device data \n\t$1\nand tracker data \n\t$2\nResults will go into\n\t$3\n"

# Manual parts that you should do first
#    - Record tracker data with scripts/record_tracker_data.py
#    - Record VIO data on device with the viotester app at the same time
#    - Pull data from device (./scripts/pull-all-viotester-data-from-device.sh)

# Strip out unnecessary parts from device data
./scripts/preprocess-vio-data.sh "$DEVICE_DATA_JSONL_FILE" "$OUTPUT_DIR"/device_vio_poses.jsonl

# Offset by first time (so that timestamps start from 0)
# (needed so that plots and sync changes work correctly)
FIRST_TIME=`head -n1 "$OUTPUT_DIR"/device_vio_poses.jsonl | jq -c ".time"`
echo "Removing $FIRST_TIME from device timestamps"
jq -c ".time = .time - $FIRST_TIME" "$OUTPUT_DIR"/device_vio_poses.jsonl \
    > "$OUTPUT_DIR"/device_vio_poses.jsonl.tmp
mv "$OUTPUT_DIR"/device_vio_poses.jsonl.tmp \
   "$OUTPUT_DIR"/device_vio_poses.jsonl

# Change VIO-space pose matrix into usual camera matrix form
# (viotester records pose in different form, see the script or README for explanation)
python ./scripts/vio_poses_to_camera_matrices.py \
    < "$OUTPUT_DIR"/device_vio_poses.jsonl \
    > "$OUTPUT_DIR"/device_camera_matrices.jsonl

# Downsample the tracker data, since it is super-high frequency (compared to VIO data)
# NOTE: tracker data might be super high-frequency, because OpenVR might be reporting interpolated poses.
./scripts/downsample.sh "$TRACKER_DOWNSAMPLE_RATE" "$TRACKER_DATA_JSONL_FILE" > \
    "$OUTPUT_DIR"/tracker_downsampled.jsonl

# Make tracker data start from t = 0
FIRST_TIME=`head -n1 "$OUTPUT_DIR"/tracker_downsampled.jsonl | jq -c ".time"`
echo "Removing $FIRST_TIME from tracker timestamps"
jq -c ".time = .time - $FIRST_TIME" "$OUTPUT_DIR"/tracker_downsampled.jsonl \
    > "$OUTPUT_DIR"/tracker_downsampled.jsonl.tmp
mv "$OUTPUT_DIR"/tracker_downsampled.jsonl.tmp \
   "$OUTPUT_DIR"/tracker_downsampled.jsonl

# Plot original trajectories
echo "Plotting non-synced non-transformed VIO trajectory vs. tracker"
python ./scripts/plot/plot_tracker_and_device.py \
    -t "$OUTPUT_DIR"/tracker_downsampled.jsonl \
    -d "$OUTPUT_DIR"/device_camera_matrices.jsonl \
    --animate \
    --animation_speed 3 \
    --loop

# Sync device data to tracker data, and transform device data to tracking space
echo "Finding time offset (sync) between device and tracker data" \
     "and transforming device poses into tracking space"
python ./scripts/align_trajectories.py \
    -t "$OUTPUT_DIR"/tracker_downsampled.jsonl \
    -d "$OUTPUT_DIR"/device_camera_matrices.jsonl \
    -o "$OUTPUT_DIR"/final_device_data.jsonl

# Plot results
echo "Plotting synced transformed VIO trajectory vs. tracker"
python ./scripts/plot/plot_tracker_and_device.py \
    -t "$OUTPUT_DIR"/tracker_downsampled.jsonl \
    -d "$OUTPUT_DIR"/final_device_data.jsonl \
    --animate \
    --animation_speed 3 \
    --loop

echo "Finished"
