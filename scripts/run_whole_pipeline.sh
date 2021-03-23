#!/bin/sh

# Just give path to the .jsonl(s) pulled from the device(s), and to the tracker data .jsonl file, and folder to work in, and this script will do all steps for aligning trajectories and time syncing

[[ -z "$1" ]] && { echo "Parameter 1 is empty" ; exit 1; }
[[ -z "$2" ]] && { echo "Parameter 2 is empty" ; exit 1; }
[[ -z "$3" ]] && { echo "Parameter 3 is empty" ; exit 1; }

DEVICE_DATA_JSONL_FILE="$1"
TRACKER_DATA_JSONL_FILE="$2"
OUTPUT_DIR="$3"

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
# TODO: cut last line, in case it is not complete?
./scripts/downsample.sh 1000 "$TRACKER_DATA_JSONL_FILE" > "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# 4. Check if there are missing data parts in tracker data (reports 'zero' pose), and remove them
# TODO: automatically remove, instead of just reporting them
printf "Reporting position jumps in $OUTPUT_DIR/tracker_data_downsampled.jsonl:\n"
python ./scripts/find_position_jumps.py -i "$OUTPUT_DIR"/tracker_data_downsampled.jsonl

# 5. Find timing (sync) to make device data and tracker data starting times match
printf "Finding time offset between device and tracker data"
python ./scripts/align_trajectories.py \
    -t "$OUTPUT_DIR"/tracker_data_downsampled.jsonl \
    -d "$OUTPUT_DIR"/device_data_time_pos_rotation_fixed_space.jsonl

# 6.

