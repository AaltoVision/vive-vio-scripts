import argparse
import json
import numpy as np
import math


def angle_between_rotations(A: np.array, B: np.array):
    R = A @ B.transpose()
    if (R - np.identity(3)).max() < 0.001:
        # print('A and B too similar')
        return 0.0
    angle = math.acos((R.trace() - 1.0) / 2.0)
    return min(angle, 2.0 * math.pi - angle)


# Note: tracker data must start before VIO data, and end after VIO data.
# (consider this when recording the dataset)


def map_vio_to_tracker_with_sync(t_VIO, t_tracker, sync):
    n_VIO = len(t_VIO)
    n_tracker = len(t_tracker)
    i_tracker = 0
    vio_to_tracker_map = [0] * n_VIO  # TODO consider numpy int array
    for i_vio in range(n_VIO):
        t = t_VIO[i_vio] + sync
        while t_tracker[i_tracker] < t and i_tracker < n_tracker - 1:
            i_tracker += 1
        vio_to_tracker_map[i_vio] = i_tracker
    return vio_to_tracker_map


def sync_rotation_diffs(t_VIO, R_VIO, t_tracker, R_tracker):
    """ TODO: port from calibrate_vio_tracker.cpp """
    sync = 0.0
    return sync

def normalized(v):
    return v / np.linalg.norm(v)

def sync_rotation_speeds(t_VIO, R_VIO, t_tracker, R_tracker):
    max_sync = (t_tracker[-1] - t_tracker[0]) - (t_VIO[-1] - t_VIO[0])
    syncs = np.linspace(0.0, max_sync, 100)

    n_VIO = len(t_VIO)
    n_tracker = len(t_tracker)

    v_VIO = np.array(
        [angle_between_rotations(R_VIO[:, :, i], R_VIO[:, :, i + 1]) for i in range(n_VIO - 1)]
    )
    v_tracker = np.array(
        [
            angle_between_rotations(R_tracker[:, :, i], R_tracker[:, :, i + 1])
            for i in range(n_tracker - 1)
        ]
    )

    i_best_sync = 0
    max_similarity = 0
    for i_sync, sync in enumerate(syncs):
        vio_to_tracker = map_vio_to_tracker_with_sync(t_VIO, t_tracker, sync)
        
        v_tracker_matched = np.array(
            [
                v_tracker[vio_to_tracker[i_VIO]] for i_VIO in range(n_VIO - 1)
            ]
        )

        similarity = np.dot(normalized(v_VIO), normalized(v_tracker_matched))
        if similarity > max_similarity:
            i_best_sync = i_sync
            max_similarity = similarity

    return syncs[i_best_sync]


def sync_movement_speeds(t_VIO, p_VIO, t_tracker, p_tracker):
    """ TODO: port from align_trajectories.py """
    sync = 0.0
    return sync


class Trajectory:
    def __init__(self):
        self.t = np.array(None)  # Timestamps (seconds)
        self.p = np.array(None)  # Positions (3xN matrix of x,y,z)
        self.r = np.array(None)  # Rotations (3x3xN matrix)


def load_trajectory(lines, pose_name):
    lines = list(lines)
    n = len(lines)
    data = Trajectory()
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


# Legacy format, should change format of tracker data so it is similar to VIO pose data
def load_tracker_data(lines):
    lines = list(lines)
    n = len(lines)
    data = Trajectory()
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


def test_map_vio_to_tracker_with_sync():
    assert map_vio_to_tracker_with_sync(
        [0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 3.0, 4.0], 0.0
    ) == [0, 1, 2]
    assert map_vio_to_tracker_with_sync(
        [0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 3.0, 4.0], 1.0
    ) == [1, 2, 3]
    assert map_vio_to_tracker_with_sync(
        [0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 3.0, 4.0], 1.9
    ) == [2, 3, 4]
    assert map_vio_to_tracker_with_sync(
        [0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 3.0, 4.0], 2.0
    ) == [2, 3, 4]
    assert map_vio_to_tracker_with_sync(
        [0.0, 1.0, 2.0], [0.0, 1.0, 2.0, 3.0, 4.0], 2.1
    ) == [3, 4, 4]


def test_angle_between_rotations():
    assert (
        angle_between_rotations(np.identity(3), np.rot90(np.identity(3))) == math.pi / 2
    )


# # TODO: might not need to treat tracker input as a separate thing from VIO inputs
# # (all are handled the same currently)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tracker_input",
        dest="tracker_input",
        help="Input file with tracker position and rotation data",
        required=True,
    )
    parser.add_argument(
        "-d",
        "--device_input",
        dest="device_input",
        help="Input file with (VIO) device poses",
        required=True,
    )
    parser.add_argument(
        "--pose_name",
        dest="pose_name",
        help="Name of pose to use in the data (VIO_pose, tag_space_pose...)",
        required=True,
    )
    args = parser.parse_args()
    with open(args.tracker_input, "r") as f:
        tracker = load_tracker_data(f)
    with open(args.device_input, "r") as f:
        vio = load_trajectory(f, args.pose_name)

    sync = 0.0

    map_vio_to_tracker_with_sync(vio.t, tracker.t, sync)

    syncs = [
        sync_movement_speeds(vio.t, vio.p, tracker.t, tracker.p),
        sync_rotation_diffs(vio.t, vio.r, tracker.t, tracker.r),
        sync_rotation_speeds(vio.t, vio.r, tracker.t, tracker.r),
    ]
    print("syncs:", syncs)

    test_map_vio_to_tracker_with_sync()
    test_angle_between_rotations()
