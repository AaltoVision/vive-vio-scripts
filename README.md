# Evaluate VIO poses against groundtruth Vive tracker poses

- (Work in progress, including this readme)

## Capturing data
- Set up your VR lighthouses according to the manufacturers instructions (for example, two Vive lighthouses in opposite corners of the tracking area, facing each other)
- (Optional) Use the 'disable_hmd_requirements.sh' script (in <i>scripts/</i>) to be able to record tracker data without having the HMD connected to the computer (for convenience)
- Use the 'tracker_start_recording.sh' script to record pose data from your VR tracker
- At the same time, record data on your other devices with the android-viotester app
- Note: 'pull-all-viotester-data-from-device.sh' and 'clear-device-datasets.sh' may be useful for managing the recording process

## Preparing the data for evaluation
- VIO data is expected to be in the form that android-viotester outputs, but does not need to be necessarily recorded with that
    - TODO explain the format
- To benchmark VIO tracking, you will first need to sync the timestamps to match the tracker recording, and you need to transform the poses from the VIO space into tracking space
- Use the run_whole_pipeline.sh script to transform VIO devices' poses into tracking space and sync each to match tracker data timestamps

## Evaluating VIO accuracy
- (TODO)
