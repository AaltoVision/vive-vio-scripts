#!/bin/bash

# Tracker recording must start before VIO recording, and must end after VIO recording
# TODO: explain setup (tag assumed to be on top of 'origin' base station with 'tag right' pointing to x- in tracking space, and 'tag up' pointing to z+ in tracking space)

# inputdir=data/viotester/recordings/arcore-20210412162821/
inputdir=data/viotester/recordings/arcore-20210412231445/

if [ ! -d $inputdir/frames ]; then
    echo "--- Extract VIO frames with ffmpeg ---"
    mkdir -p $inputdir/frames
    ffmpeg -i $inputdir/data.avi -start_number 0 $inputdir/frames/%d.png -hide_banner
fi
if [ ! -f calib_data/vio.jsonl ]; then
    echo "--- Preprocess VIO data ---"
    mkdir -p calib_data
    cmake --build ./libs/tagbench/build --target input_data_preprocessor --config RelWithDebInfo
    ./libs/tagbench/build/RelWithDebInfo/input_data_preprocessor.exe -i $inputdir -o calib_data/vio.jsonl -n arcore

fi
if [ ! -f calib_data/vio_camera_matrices.jsonl ]; then
    echo "--- Make version of vio.jsonl with camera matrices, for plotting ---"
    ./scripts/preprocess-vio-data.sh $inputdir/data.jsonl calib_data/vio_temp.jsonl
    python ./scripts/vio_poses_to_camera_matrices.py \
        < calib_data/vio_temp.jsonl \
        > calib_data/vio_camera_matrices.jsonl
    rm calib_data/vio_temp.jsonl
    FIRST_TIME=`head -n1 calib_data/vio_camera_matrices.jsonl | jq -c ".time"`
    jq -c ".time = .time - $FIRST_TIME" calib_data/vio_camera_matrices.jsonl \
        > calib_data/vio_camera_matrices.jsonl.tmp
    mv calib_data/vio_camera_matrices.jsonl.tmp calib_data/vio_camera_matrices.jsonl

    FIRST_TIME=`head -n1 calib_data/ds100_trackerstartaligned.jsonl | jq -c ".time"`
    jq -c ".time = .time - $FIRST_TIME" calib_data/ds100_trackerstartaligned.jsonl \
        > calib_data/ds100_trackerstartaligned_minusfirst.jsonl

    OUTPUT_DIR=calib_data/
    python ./scripts/align_trajectories.py \
        -t "$OUTPUT_DIR"/ds100_trackerstartaligned.jsonl \
        -d "$OUTPUT_DIR"/vio_camera_matrices.jsonl \
        -o "$OUTPUT_DIR"/final_device_data.jsonl
fi

# calibrator_build_type=Debug
calibrator_build_type=RelWithDebInfo
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
    --vio calib_data/vio.jsonl \
    --tracker calib_data/ds100_trackerstartaligned.jsonl && \
echo "--- Done ---"
