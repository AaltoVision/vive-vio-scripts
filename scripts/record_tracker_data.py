import openvr as vr
import time
import json

def main():
    vr_system = vr.init(vr.VRApplication_Background)

    trackers = []
    for i in range(vr.k_unMaxTrackedDeviceCount):
        device_class = vr_system.getTrackedDeviceClass(i)
        if device_class == vr.TrackedDeviceClass_GenericTracker:
            trackers.append(i)

    poses = []
    t_start = time.time()
    while True:
        t_now = time.time()
        poses = vr_system.getDeviceToAbsoluteTrackingPose(vr.TrackingUniverseSeated, 0.0, poses)
        for i in trackers:
            m = poses[i].mDeviceToAbsoluteTracking
            j = {}
            j["time"] = t_now
            j["tracker"] = i
            j["position"] = { "x": m[0][3], "y": m[1][3], "z": m[2][3] }
            j["rotation"] = {
                "col0": [ m[0][0], m[0][1], m[0][2], ],
                "col1": [ m[1][0], m[1][1], m[1][2], ],
                "col2": [ m[2][0], m[2][1], m[2][2], ],
            }
            print(json.dumps(j))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Recording ended by pressing Ctrl+C, which raises KeyboardInterrupt
        pass