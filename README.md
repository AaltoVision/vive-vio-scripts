# Scripts for recording Vive tracker data, syncing with VIO (Visual inertial odometry) data, and calibrating tracker and VIO devices

- Work in progress, including this readme
- See <i>scripts/new_calibrate.sh</i> for scripts that use VIO data with an Apriltag in the frames, and use that for syncing VIO and tracker data, and finding calibration matrix between (note: calibration does not work yet)
- See <i>scripts/run_whole_pipeline.sh</i> for scripts that use VIO pose data (not camera images at all) for finding sync between VIO and tracker data
- scripts/calibrate_tracker_and_vio.sh is outdated but might be a useful reference; new_calibrate.sh is basically newer version of that
- See <i>requirements.txt</i> for required Python packages
- Notes about current implementation status
  - Have a couple methods of syncing data, that is, finding time offset between tracker recording starting and VIO-data recording start time, see src/sync.py, sync_* functions
  - Could not get calibration (finding tracker position & orientation in VIO device local space, or inverse of that) working yet. Worked out the math for finding the position from two pose correspondences (tracker and VIO pose data from two timestamps), but could not get the implementation working yet.
  - Many of the scripts (both *.sh and *.py) are probably most useful as a reference for ideas. Many things are unfinished (calibration) or not robust yet, and due to expecting data in different forms, for example android-viotester vs. tracker vs. preprocessed data formats, the scripts are not always compatible. Do not be afraid of taking pieces from here and there to make something new for your exact use case.
  - Some of the code in the repo is C++ , but those parts are rather simple and should be redone in python for easier setup and more rapid development
    - libs/calibrate_vio_tracker currently serves as reference for calibration code and syncing by rotation speeds and should be deleted soon
    - libs/find_tag_space_poses just uses OpenCV's solvePnP to find VIO pose relative to Apriltag in the camera image (homography), and would be easier to use as a python script. Actually the Apriltag library itself seems to have functionality for getting the homography matrix out, so changing input_data_preprocessor to output homography matrices should make this program obsolete.
    - libs/tagbench/ is used for the input_data_preprocessor part for transforming VIO data a bit and detecting Apriltags in camera images. This might be worth keeping as-is, because the Apriltag library might not be easily available in python.

## Data formats

- Original VIO data looks like this (recorded with [Android VIO-tester](https://github.com/AaltoML/android-viotester)):

        ...
        {"sensor":{"type":"accelerometer","values":[2.2925679683685303,-1.5601439476013184,9.72916030883789]},"time":989850.0673587171}
        {"sensor":{"type":"gyroscope","values":[0.02761712484061718,0.009785706177353859,0.0999743640422821]},"time":989850.065808717}
        {"frames":[{"cameraInd":0,"cameraParameters":{"focalLengthX":1448.4306640625,"focalLengthY":1449.7490234375,"principalPointX":944.5816040039063,"principalPointY":535.9908447265625},"number":0,"time":0.01}],"number":0,"time":0.01}
        {"sensor":{"type":"gyroscope","values":[0.026552125811576843,0.008720706216990948,0.09784336388111115]},"time":989850.0683293421}
        ...
        {"arcore":{"orientation":{"w":0.7590118646621704,"x":0.5861769914627075,"y":-0.1766176074743271,"z":-0.22159355878829956},"position":{"x":-0.01184267457574606,"y":0.007641160394996405,"z":0.005758402869105339}},"time":989851.1044255381}
        ...


- The 'input_data_preprocessor' from the 'tagbench' project is used for matching the VIO pose data with matching camera frames, since the original VIO data has them as separate lines of data. 'input_data_preprocessor' also detects Apriltag markers from the frames, if they are present, and adds the 'markers' field which holds the (x, y) pixel coordinates of marker corners.

- VIO data after running it through 'input_data_preprocessor':

        {"cameraExtrinsics":{"orientation":{"w":0.7590492963790894,"x":0.5859752893447876,"y":-0.17576880753040314,"z":-0.22267122566699982},"position":{"x":-0.014251479879021645,"y":0.008731266483664513,"z":0.0031209520529955626}},"cameraIntrinsics":{"focalLengthX":1448.4306640625,"focalLengthY":1449.7490234375,"principalPointX":944.5816040039063,"principalPointY":535.9908447265625},"frameHeight":1080,"frameIndex":28,"framePath":"data/viotester/recordings/arcore-20210416121646/frames\\28.png","markers":[[[1085.56689453125,285.15753173828136],[1159.9771728515623,279.94213867187494],[1150.3148193359375,206.7359771728515],[1075.6259765625,211.40354919433597]]],"time":989851.125}
        {"cameraExtrinsics":{"orientation":{"w":0.7605444192886353,"x":0.5837897658348083,"y":-0.17268887162208557,"z":-0.22569938004016876},"position":{"x":-0.013904094696044922,"y":0.007861300371587276,"z":0.0023557774256914854}},"cameraIntrinsics":{"focalLengthX":1448.4306640625,"focalLengthY":1449.7490234375,"principalPointX":944.5816040039063,"principalPointY":535.9908447265625},"frameHeight":1080,"frameIndex":30,"framePath":"data/viotester/recordings/arcore-20210416121646/frames\\30.png","markers":[[[1069.6826171875,290.3877258300782],[1143.8404541015625,285.4081420898437],[1134.124755859375,212.30039978027344],[1059.8919677734375,216.5612182617188]]],"time":989851.1875}
        ...

- The script 'vio_poses_to_camera_matrices.py' changes the pose into the usual camera matrix format, M = (R | t), where R is a 3x3 rotation matrix, t is the position. Original position stored in viotester data is in -R.inverse()*t, instead of t, while rotation is just the quaternion for R.inverse().

- <i>scripts/tracker/record_tracker_data.py</i> records tracker data in this kind of format (note: currently the script queries poses from OpenVR as fast as it can, which results in multiple lines having same timestamps; this is probably interpolated data, might be a good idea to limit the sampling rate in the script a bit):

        {"time": 1618564605.4081042, "tracker": 1, "position": {"x": 0.0435674712061882, "y": 0.512598991394043, "z": -0.2645307183265686}, "rotation": {"col0": [-0.970168948173523, -0.14467093348503113, 0.19453148543834686], "col1": [0.1705111265182495, 0.16320247948169708, 0.9717463254928589], "col2": [-0.17233146727085114, 0.9759278893470764, -0.13366597890853882]}}
        {"time": 1618564605.4081042, "tracker": 1, "position": {"x": 0.04356811195611954, "y": 0.5125971436500549, "z": -0.2645290195941925}, "rotation": {"col0": [-0.9701678156852722, -0.14467042684555054, 0.19453749060630798], "col1": [0.17051810026168823, 0.1631973534822464, 0.9717459678649902], "col2": [-0.17233090102672577, 0.9759288430213928, -0.13365989923477173]}}

- Note: rotation should probably be an array of rows, or a quaternion, instead of having "colN" fields for each column.

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
- Note: some of the tracker-VIO time-syncing scripts assume VIO data recording starts after tracker recording starts, and ends before tracker recording ends. So, always start recording tracker data, then start recording VIO data, then stop recording VIO data, then stop recording tracker data.

## Preparing the data
- VIO data is expected to be in the form that android-viotester outputs, but does not need to be necessarily recorded with that
- To benchmark VIO tracking, you will first need to sync the timestamps to match the tracker recording, and you need to transform the poses from the VIO space into tracking space
- Use the <i>run_whole_pipeline.sh</i> script to transform VIO devices' poses into tracking space and sync each to match tracker data timestamps
- Note: this section is about syncing VIO and tracker data, but not calibration. See the 'Notes about current implementation status' part of the readme for purposes of the different shell scripts.
