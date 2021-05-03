# Record VIO trajectories with Vive tracker groundtruth

- Work in progress, including this readme
- See <i>scripts/new_calibrate.sh</i> for scripts that use VIO data with an Apriltag in the frames, and use that for syncing VIO and tracker data, and finding calibration matrix between (note: calibration does not work yet)
- See <i>scripts/run_whole_pipeline.sh</i> for scripts that use VIO pose data (not camera images at all) for finding sync between VIO and tracker data
- scripts/calibrate_tracker_and_vio.sh is outdated but might be a useful reference; new_calibrate.sh is basically newer version of that
- See <i>requirements.txt</i> for required Python packages
- Notes about current implementation status
  - Have a couple methods of syncing data, that is, finding time offset between tracker recording starting and VIO-data recording start time, see src/sync.py, sync_* functions
  - Could not get calibration (finding tracker position & orientation in VIO device local space, or inverse of that) working yet. Worked out the math for finding the position from two pose correspondences (tracker and VIO pose data from two timestamps), but could not get the implementation working yet.
  - Many of the scripts (both *.sh and *.py) are probably most useful as a reference for ideas. Many things are unfinished (calibration) or not robust yet, and due to expecting data in different forms, for example android-viotester vs. tracker vs. preprocessed data formats, the scripts are not always compatible. Do not be afraid of taking pieces from here and there to make something new for your exact use case.

## Data formats

- Original VIO data looks like this:

- The 'input_data_preprocessor' from the 'tagbench' project is used for matching the VIO pose data with matching camera frames, since the original VIO data (recorded with android-viotester) has them as separate lines of data. 'input_data_preprocessor' also detects Apriltag markers from the frames, if they are present, and adds the 'markers' field which holds the (x, y) pixel coordinates of marker corners.

- VIO data after running it through 'input_data_preprocessor':

- The script 'vio_poses_to_camera_matrices.py' changes the pose into the usual camera matrix format, M = (R | t), where R is a 3x3 rotation matrix, t is the position. Original position stored in viotester data is in -R.inverse()*t, instead of t, while rotation is just the quaternion for R.inverse().


## Setting up Vive
- Download and run [Vive setup](https://www.vive.com/us/setup/)
    - Make sure to install the appropriate drivers for your HMD in Viveport, after it has finished installing
- (Optional) Use the <i>disable_hmd_requirements.sh</i> script to be able to record tracker data without having the HMD connected to the computer, for convenience
- Set up your VR base stations according to the manufacturers instructions. For example, Vive with two base stations:
    - Place base stations in opposite corners of the tracking area, facing each other
    - Connect power to the base stations
    - Use the button on the back of the base stations to change channels; one should show 'b' and the other 'c' on the front side LED
- For just recording tracker data, you should not need to do SteamVR's Room Setup
- Start SteamVR on the computer
- Connect the Vive tracker's USB dongle, then pair it to the computer (<i>SteamVR->Devices->Pair Controller</i>)
- SteamVR window should show that two base stations and a tracker are connected

## Capturing data
- Use the <i>record_tracker_data.py</i> script to record pose data from your VR tracker
    - Press Ctrl+C to stop recording
- Record data on your other devices with the android-viotester app or by other means
- Note: <i>pull-all-viotester-data-from-device.sh</i> and <i>clear-device-datasets.sh</i> may be useful for managing the recording process

## Preparing the data
- VIO data is expected to be in the form that android-viotester outputs, but does not need to be necessarily recorded with that
- To benchmark VIO tracking, you will first need to sync the timestamps to match the tracker recording, and you need to transform the poses from the VIO space into tracking space
- Use the <i>run_whole_pipeline.sh</i> script to transform VIO devices' poses into tracking space and sync each to match tracker data timestamps
