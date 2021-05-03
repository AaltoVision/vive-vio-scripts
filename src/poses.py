import numpy as np
import json

# _to_camera_matrices stuff?

class Poses:
    def __init__(self):
        self.t = np.array(None)  # Timestamps (seconds)
        self.p = np.array(None)  # Positions (3xN matrix of x,y,z)
        self.r = np.array(None)  # Rotations (3x3xN matrix)


def load_poses(lines, pose_name):
    lines = list(lines)
    n = len(lines)
    data = Poses()
    data.t = np.zeros(n)
    data.p = np.zeros((3, n))
    data.r = np.zeros((3, 3, n))
    for i, line in enumerate(lines):
        j = json.loads(line)
        data.t[i] = j["time"]

        pose = np.array(j[pose_name])
        assert pose.shape == (3, 4)

        data.p[:, i] = pose[:, 3]
        data.r[:, :, i] = pose[0:3, 0:3]
    return data


# Legacy format, should change format of tracker data so it is similar to VIO pose data, so it will be easier to handle both
def load_tracker_data(lines):
    lines = list(lines)
    n = len(lines)
    data = Poses()
    data.t = np.zeros(n)
    data.p = np.zeros((3, n))
    data.r = np.zeros((3, 3, n))
    for i, line in enumerate(lines):
        j = json.loads(line)
        data.t[i] = j["time"]
        data.p[:, i] = [
            j["position"]["x"],
            j["position"]["y"],
            j["position"]["z"],
        ]
        if "rotation" in j:
            data.r[:, 0, i] = j["rotation"]["col0"]
            data.r[:, 1, i] = j["rotation"]["col1"]
            data.r[:, 2, i] = j["rotation"]["col2"]
    return data

