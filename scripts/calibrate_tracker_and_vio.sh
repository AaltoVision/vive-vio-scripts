#!/bin/bash

# Tracker recording must start before VIO recording, and must end after VIO recording
# TODO: explain setup (tag assumed to be on top of 'origin' base station with 'tag right' pointing to x- in tracking space, and 'tag up' pointing to z+ in tracking space)

# INPUT_DIR=data/viotester/recordings/arcore-20210412162821/
INPUT_DIR=data/viotester/recordings/arcore-20210416121646/
OUTPUT_DIR=data/moremovement/
TRACKER_JSONL="$OUTPUT_DIR"/tracker.jsonl
TRACKER_DOWNSAMPLING=100

if [ ! -d $INPUT_DIR/frames ]; then
    echo "--- Extract VIO frames with ffmpeg ---"
    mkdir -p $INPUT_DIR/frames
    ffmpeg -i $INPUT_DIR/data.avi -start_number 0 $INPUT_DIR/frames/%d.png -hide_banner
fi
if [ ! -f $OUTPUT_DIR/vio.jsonl ]; then
    echo "--- Preprocess VIO data ---"
    # - Detect tag corners in the images ('markers' data in the output)
    # - Join VIO pose, intrinsic and frame data by timestamp
    mkdir -p $OUTPUT_DIR
    cmake --build ./libs/tagbench/build --target input_data_preprocessor --config RelWithDebInfo
    ./libs/tagbench/build/RelWithDebInfo/input_data_preprocessor.exe -i $INPUT_DIR -o $OUTPUT_DIR/vio.jsonl -n arcore

fi
if [ ! -f $OUTPUT_DIR/vio_camera_matrices.jsonl ]; then
    # TODO this is a bit weird, outdated
    echo "--- Make version of vio.jsonl with camera matrices, for plotting ---"
    # - Original android-viotester output poses are in different format, so we change into
    # usual camera matrix (= [R|t] pose matrix) style, to match tracker data
    ./scripts/preprocess-vio-data.sh $INPUT_DIR/data.jsonl $OUTPUT_DIR/vio_temp.jsonl
    python ./scripts/vio_poses_to_camera_matrices.py \
        < $OUTPUT_DIR/vio_temp.jsonl \
        > $OUTPUT_DIR/vio_camera_matrices.jsonl
    rm $OUTPUT_DIR/vio_temp.jsonl

    # Remove first timestamp t0 from all timestamps
    FIRST_TIME=`head -n1 $OUTPUT_DIR/vio_camera_matrices.jsonl | jq -c ".time"`
    jq -c ".time = .time - $FIRST_TIME" $OUTPUT_DIR/vio_camera_matrices.jsonl \
        > $OUTPUT_DIR/vio_camera_matrices.jsonl.tmp
    mv $OUTPUT_DIR/vio_camera_matrices.jsonl.tmp $OUTPUT_DIR/vio_camera_matrices.jsonl

    # Remove first timestamp t0 from all timestamps
    FIRST_TIME=`head -n1 $TRACKER_JSONL | jq -c ".time"`
    jq -c ".time = .time - $FIRST_TIME" $TRACKER_JSONL \
        > $OUTPUT_DIR/tracker_minusfirst.jsonl
fi
if [ ! -f "$OUTPUT_DIR"/ds$TRACKER_DOWNSAMPLING_tracker_minusfirst.jsonl ]; then
    ./scripts/downsample.sh $TRACKER_DOWNSAMPLING "$OUTPUT_DIR"/tracker_minusfirst.jsonl \
        > "$OUTPUT_DIR"/ds$TRACKER_DOWNSAMPLING_tracker_minusfirst.jsonl
fi
if [ ! -f $OUTPUT_DIR/vio_camera_matrices_automatically_aligned.jsonl ]; then
    python ./scripts/align_trajectories.py \
        -t "$OUTPUT_DIR"/ds$TRACKER_DOWNSAMPLING_tracker_minusfirst.jsonl \
        -d "$OUTPUT_DIR"/vio_camera_matrices.jsonl \
        -o "$OUTPUT_DIR"/vio_camera_matrices_automatically_aligned.jsonl
fi

# CUSTOM_SYNC=2.96
# jq -c ".time = .time + $CUSTOM_SYNC" $OUTPUT_DIR/vio_camera_matrices.jsonl \
#     > $OUTPUT_DIR/vio_camera_matrices_with_sync_$CUSTOM_SYNC.jsonl
# python ./scripts/plot_tracker_and_device.py \
#     -t "$OUTPUT_DIR"/ds$TRACKER_DOWNSAMPLING_trackerstartaligned_minusfirst.jsonl \
#     -d "$OUTPUT_DIR"/vio_camera_matrices_with_sync_$CUSTOM_SYNC.jsonl \
#     --animate \
#     --animation_speed 1 \
#     --loop

calibrator_build_type=Debug
# calibrator_build_type=RelWithDebInfo
# calibrator_build_type=Release
opencv_build_path=~/code/work_cv/refs/opencv/build/

if [ ! -d libs/calibrate_vio_tracker/build ]; then
    echo "--- Generate calibrate_vio_tracker CMake build ---"
    cmake -Hlibs/calibrate_vio_tracker -Blibs/calibrate_vio_tracker/build -DCMAKE_PREFIX_PATH=$opencv_build_path
    mkdir -p libs/calibrate_vio_tracker/build
    mkdir -p libs/calibrate_vio_tracker/build/{Debug,RelWithDebInfo,Release}
    cp $opencv_build_path/x64/vc15/bin/opencv_world451d.dll libs/calibrate_vio_tracker/build/Debug/
    cp $opencv_build_path/x64/vc15/bin/opencv_world451.dll libs/calibrate_vio_tracker/build/RelWithDebInfo/
    cp $opencv_build_path/x64/vc15/bin/opencv_world451.dll libs/calibrate_vio_tracker/build/Release/
fi
echo "--- Build ---" && \
time cmake --build libs/calibrate_vio_tracker/build --config $calibrator_build_type && \
echo "--- Calibrate ---" && \
time libs/calibrate_vio_tracker/build/$calibrator_build_type/calibrate_vio_tracker.exe \
    --vio $OUTPUT_DIR/vio.jsonl \
    --test \
    --tracker $OUTPUT_DIR/ds$TRACKER_DOWNSAMPLING_tracker_minusfirst.jsonl && \
echo "--- Done ---"
