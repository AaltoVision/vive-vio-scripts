#!/bin/bash

set -e

INPUT_DIR=data/viotester/recordings/arcore-20210416121646/
OUTPUT_DIR=data/new_calib_moremovement/
TRACKER_JSONL=data/new_calib_moremovement/tracker.jsonl
TRACKER_DOWNSAMPLING=100
OPENCV_BUILD_PATH=~/code/work_cv/refs/opencv/build/

if [ ! -d $INPUT_DIR/frames ]; then
    echo "--- Extract VIO frames with ffmpeg ---"
    mkdir -p $INPUT_DIR/frames
    ffmpeg -i $INPUT_DIR/data.avi -start_number 0 $INPUT_DIR/frames/%d.png -hide_banner
fi

if [ ! -d libs/tagbench/build ]; then
    echo "--- Generate tagbench (input_data_preprocessor) CMake build ---"
    cmake -Hlibs/tagbench -Blibs/tagbench/build -DCMAKE_PREFIX_PATH=$OPENCV_BUILD_PATH
    mkdir -p libs/tagbench/build
    mkdir -p libs/tagbench/build/{Debug,RelWithDebInfo,Release}
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451d.dll libs/tagbench/build/Debug/
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451.dll libs/tagbench/build/RelWithDebInfo/
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451.dll libs/tagbench/build/Release/
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
    echo "--- Make version of vio.jsonl with camera matrices, for plotting ---"
    # - Original android-viotester output poses are in different format, so we change into
    # usual camera matrix (= [R|t] pose matrix) style, to match tracker data
    python ./scripts/preprocessed_vio_poses_to_camera_matrices.py \
        < $OUTPUT_DIR/vio.jsonl \
        > $OUTPUT_DIR/vio_camera_matrices.jsonl

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

if [ ! -f "$OUTPUT_DIR"/ds"$TRACKER_DOWNSAMPLING"_tracker_minusfirst.jsonl ]; then
    ./scripts/downsample.sh $TRACKER_DOWNSAMPLING "$OUTPUT_DIR"/tracker_minusfirst.jsonl \
        > "$OUTPUT_DIR"/ds"$TRACKER_DOWNSAMPLING"_tracker_minusfirst.jsonl
fi

# # if [ ! -f $OUTPUT_DIR/vio_camera_matrices_automatically_aligned.jsonl ]; then
# #     python ./scripts/align_trajectories.py \
# #         -t "$OUTPUT_DIR"/ds"$TRACKER_DOWNSAMPLING"_tracker_minusfirst.jsonl \
# #         -d "$OUTPUT_DIR"/vio_camera_matrices.jsonl \
# #         -o "$OUTPUT_DIR"/vio_camera_matrices_automatically_aligned.jsonl
# # fi

build_config=Debug
# build_config=RelWithDebInfo
# build_config=Release

if [ ! -d libs/find_tag_space_poses/build ]; then
    echo "--- Generate find_tag_poses CMake build ---"
    cmake -Hlibs/find_tag_space_poses -Blibs/find_tag_space_poses/build -DCMAKE_PREFIX_PATH=$OPENCV_BUILD_PATH
    mkdir -p libs/find_tag_space_poses/build
    mkdir -p libs/find_tag_space_poses/build/{Debug,RelWithDebInfo,Release}
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451d.dll libs/find_tag_space_poses/build/Debug/
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451.dll libs/find_tag_space_poses/build/RelWithDebInfo/
    cp $OPENCV_BUILD_PATH/x64/vc15/bin/opencv_world451.dll libs/find_tag_space_poses/build/Release/
fi

echo "--- Build find_tag_poses ---"
time cmake --build libs/find_tag_space_poses/build \
    --config $build_config \
    --target find_tag_space_poses

if [ ! -f $OUTPUT_DIR/vio_with_tag_space_poses.jsonl ]; then
    echo "--- Find tag space poses ---"
    time libs/find_tag_space_poses/build/$build_config/find_tag_space_poses.exe \
        -i $OUTPUT_DIR/vio_camera_matrices.jsonl \
        -o $OUTPUT_DIR/vio_with_tag_space_poses.jsonl \
        -s 0.025
fi

echo "--- Sync and calibrate ---"
python src/sync.py \
    -d $OUTPUT_DIR/vio_with_tag_space_poses.jsonl \
    -t $OUTPUT_DIR/ds"$TRACKER_DOWNSAMPLING"_tracker_minusfirst.jsonl \
    --pose_name tag_space_pose

echo "--- Done ---"
