import argparse
import openvr as vr
import time
import json

# Just a quick helper tool for understanding and validating the tracker coordinate system
# Write a name (such as 'upside down'), then press enter and it will record a pose with that name

def main(output_file):
    vr_system = vr.init(vr.VRApplication_Background)

    trackers = []
    for i in range(vr.k_unMaxTrackedDeviceCount):
        device_class = vr_system.getTrackedDeviceClass(i)
        if device_class == vr.TrackedDeviceClass_GenericTracker:
            trackers.append(i)

    poses = []
    t_start = time.time()
    while True:
        name = input("Pose name (Ctrl+C to stop): ")
        t_now = time.time()
        poses = vr_system.getDeviceToAbsoluteTrackingPose(vr.TrackingUniverseSeated, 0.0, poses)
        for i in trackers:
            m = poses[i].mDeviceToAbsoluteTracking
            j = {}
            j["time"] = t_now
            j["name"] = name
            j["tracker"] = i
            j["position"] = { "x": m[0][3], "y": m[1][3], "z": m[2][3] }
            j["rotation"] = {
                "col0": [ m[0][0], m[0][1], m[0][2], ],
                "col1": [ m[1][0], m[1][1], m[1][2], ],
                "col2": [ m[2][0], m[2][1], m[2][2], ],
            }
            j_string = json.dumps(j)
            print(j_string)
            if output_file is not None:
                output_file.write(j_string + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        help="Output file to write the data to (without the pose name prompt)",
    )
    args = parser.parse_args()
    output_file = None
    if args.output:
        output_file = open(args.output, 'w')
    try:
        main(output_file)
    except KeyboardInterrupt:
        # Recording ended by pressing Ctrl+C, which raises KeyboardInterrupt
        if output_file is not None:
            output_file.close()