# Record VIO trajectories with Vive tracker groundtruth

- (Work in progress, including this readme)
- See <i>run_whole_pipeline.sh</i> for a quick usage example
- See <i>requirements.txt</i> for required Python packages

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
    - (TODO: explain the format here)
- To benchmark VIO tracking, you will first need to sync the timestamps to match the tracker recording, and you need to transform the poses from the VIO space into tracking space
- Use the <i>run_whole_pipeline.sh</i> script to transform VIO devices' poses into tracking space and sync each to match tracker data timestamps
