#!/bin/sh

# Just give path to the .jsonl(s) pulled from the device(s), and to the tracker data .jsonl file, and folder to work in, and this script will do all steps for aligning trajectories and time syncing

[[ -z "$1" ]] && { echo "Parameter 1 (device data jsonl file) is missing" ; exit 1; }
[[ -z "$2" ]] && { echo "Parameter 2 (tracker data jsonl file) is missing" ; exit 1; }
[[ -z "$3" ]] && { echo "Parameter 3 (output dir) is missing" ; exit 1; }

DEVICE_DATA_JSONL_FILE="$1"
TRACKER_DATA_JSONL_FILE="$2"
OUTPUT_DIR="$3"

TRACKER_DOWNSAMPLE_RATE=1000

printf "Using device data \n\t$1\nand tracker data \n\t$2\nResults will go into\n\t$3\n"

# 0. Manual parts that you should do first
#    - Record tracker data with ./scripts/tracker_start_recording.sh
#    - Record VIO data on device with the viotester app at the same time
#    - Pull data from device (./scripts/pull-all-viotester-data-from-device.sh)

# 1. Strip out unnecessary parts from device data
./scripts/preprocess-vio-data.sh "$DEVICE_DATA_JSONL_FILE" "$OUTPUT_DIR"/device_data_time_pos_orientation_vio_space.jsonl

# 2. Change VIO-space pose matrix into usual camera matrix form
python ./scripts/arcore_view_matrices_to_camera_matrices.py \
    < "$OUTPUT_DIR"/device_data_time_pos_orientation_vio_space.jsonl \
    > "$OUTPUT_DIR"/device_data_time_pos_rotation_fixed_space.jsonl

# 3. Downsample the tracker data, since it is super-high frequency (compared to VIO data)
# Also cut out last line from tracker data, as it may be incomplete
cp "$TRACKER_DATA_JSONL_FILE" "$OUTPUT_DIR"/tracker_data_no_last_line.jsonl
sed -i '$d' "$OUTPUT_DIR"/tracker_data_no_last_line.jsonl
./scripts/downsample.sh "$TRACKER_DOWNSAMPLE_RATE" "$OUTPUT_DIR"/tracker_data_no_last_line.jsonl > "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# 4. Check if there are missing data parts in tracker data (reports 'zero' pose), and remove them
# TODO: automatically remove, instead of just reporting them
echo "Reporting position jumps in $OUTPUT_DIR/tracker_data_downsampled.jsonl:"
python ./scripts/find_position_jumps.py -i "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# # TEMPORARY, delete line 1339 onwards (zeroes)
# sed -i '1339,$d' "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# echo "TEMPORARY DEV STEP: remove first 4 seconds of tracker data"
# jq -c 'select(.time>4.0)' "$OUTPUT_DIR"/tracker_data_downsampled.jsonl > "$OUTPUT_DIR"/tracker_missing_3s.jsonl
# mv "$OUTPUT_DIR"/tracker_missing_3s.jsonl "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# TODO: possibly make device data start from t=0? or maybe not, if there are many devices then original t is useful (they probably have nearly same clocks)
# TODO: actually, if we just record world time data in the tracker data, that would make lots of sense...

# 5. Plot results original trajectories
echo "Plotting results non-synced non-transformed results"
python ./scripts/plot_tracker_and_device.py \
    -t "$OUTPUT_DIR"/tracker_data_downsampled.jsonl \
    -d "$OUTPUT_DIR"/device_data_time_pos_rotation_fixed_space.jsonl \
    --animate \
    --animation_speed 3 \
    --loop

# # 6. Find timing (sync) to make device data and tracker data starting times match
# echo "Finding time offset between device and tracker data"
# python ./scripts/align_trajectories.py \
#     -t "$OUTPUT_DIR"/tracker_data_downsampled.jsonl \
#     -d "$OUTPUT_DIR"/device_data_time_pos_rotation_fixed_space.jsonl

# X.
# - Plot original trajectories
# - Find timing through biggest distance spike (simple, for now)
# - Plot trajectories but using the timing sync
# - Find M, not global optimization but just from that spike (or right before, or right after?)
# - Transform device data into tracker space with M
# - Plot tracker trajectory and transformed-into-tracker-space device trajectory
echo "Finding time offset between device and tracker data"
python ./scripts/align_trajectories.py \
    -t "$OUTPUT_DIR"/tracker_data_downsampled.jsonl \
    -d "$OUTPUT_DIR"/device_data_time_pos_rotation_fixed_space.jsonl \
    -o "$OUTPUT_DIR"/final_device_data.jsonl

echo "Plotting results synced transformed results"
python ./scripts/plot_tracker_and_device.py \
    -t "$OUTPUT_DIR"/tracker_data_downsampled.jsonl \
    -d "$OUTPUT_DIR"/final_device_data.jsonl \
    --animate \
    --animation_speed 3 \
    --loop

echo "Finished"



