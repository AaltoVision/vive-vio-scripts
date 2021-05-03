import argparse
import json
import numpy as np
import math
from poses import *


def normalized(v):
    return v / np.linalg.norm(v)


def angle_between_rotations(A: np.array, B: np.array):
    R = A @ B.transpose()
    if (R - np.identity(3)).max() < 0.001:
        # print('A and B too similar')
        return 0.0
    angle = math.acos((R.trace() - 1.0) / 2.0)
    return min(angle, 2.0 * math.pi - angle)


def movement_speeds(t, p):
    dts = t[1:-1] - t[0:-2]
    dps = p[:, 1:-1] - p[:, 0:-2]
    ds = np.linalg.norm(dps, axis=0, keepdims=True)
    print('dsshape', ds.shape)
    return ds / dts


# Note: tracker data must start before VIO data, and end after VIO data.
# (consider this when recording the dataset)


def map_vio_to_tracker_with_sync(t_vio, t_tracker, sync):
    n_vio = len(t_vio)
    n_tracker = len(t_tracker)
    i_tracker = 0
    vio_to_tracker_map = [0] * n_vio  # TODO consider numpy int array
    for i_vio in range(n_vio):
        # Add sync to VIO timestamp; 1.0s sync means
        # VIO track starts 1 sec after tracker started recording
        t = t_vio[i_vio] + sync
        # Seek to first tracker timestamp that is greater-or-equal
        # to the synced VIO timestamp
        while t_tracker[i_tracker] < t and i_tracker < n_tracker - 1:
            i_tracker += 1
        vio_to_tracker_map[i_vio] = i_tracker
    return vio_to_tracker_map


def sync_rotation_diffs(t_vio, R_vio, t_tracker, R_tracker):
    """TODO: port from calibrate_vio_tracker.cpp"""
    sync = 0.0
    return sync


def sync_rotation_speeds(t_vio, R_vio, t_tracker, R_tracker):
    """Find sync by comparing rotation speeds"""
    max_sync = (t_tracker[-1] - t_tracker[0]) - (t_vio[-1] - t_vio[0])
    syncs = np.linspace(0.0, max_sync, 100)

    n_vio = len(t_vio)
    n_tracker = len(t_tracker)

    v_vio = np.array(
        [
            angle_between_rotations(R_vio[:, :, i], R_vio[:, :, i + 1])
            for i in range(n_vio - 1)
        ]
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
        vio_to_tracker = map_vio_to_tracker_with_sync(t_vio, t_tracker, sync)

        v_tracker_matched = np.array(
            [v_tracker[vio_to_tracker[i_vio]] for i_vio in range(n_vio - 1)]
        )

        similarity = np.dot(normalized(v_vio), normalized(v_tracker_matched))
        if similarity > max_similarity:
            i_best_sync = i_sync
            max_similarity = similarity

    return syncs[i_best_sync]


def sync_movement_speeds(t_vio, p_vio, t_tracker, p_tracker):
    """TODO: port from align_trajectories.py"""
    """TODO: test it again here after porting"""

    # def sync_errors(sync: float, N: int):
    #     # Find M from Nth tracker frame
    #     M_tracker = np.identity(4)
    #     M_tracker[0:3, 3] = tracker.ps[0:3, N]
    #     M_tracker[:3, 0] = tracker.frame_xs[:3, N]
    #     M_tracker[:3, 1] = tracker.frame_ys[:3, N]
    #     M_tracker[:3, 2] = tracker.frame_zs[:3, N]
    #     # print(M_tracker)

    #     corresponding_device_N = tracker_idx_to_device_idx(N, sync)
    #     # print('corresponding_device_N', corresponding_device_N)
    #     M_device = np.identity(4)
    #     M_device[0:3, 3] = device.ps[0:3, corresponding_device_N]
    #     M_device[:3, 0] = device.frame_xs[:3, corresponding_device_N]
    #     M_device[:3, 1] = device.frame_ys[:3, corresponding_device_N]
    #     M_device[:3, 2] = device.frame_zs[:3, corresponding_device_N]
    #     # print(M_device)
    #     # NOTE ds should be scaled by (ts[n] - ts[n-1]), since sampling freq is different

    #     M_device_to_tracker = M_tracker @ np.linalg.inv(M_device)
    #     errors = []
    #     transform_test_indices = [10 * x for x in range(100)]
    #     for tracker_idx in transform_test_indices:
    #         device_idx = tracker_idx_to_device_idx(tracker_idx, sync)
    #         tracker_point = tracker.ps[0:3, tracker_idx]
    #         device_test_point = device.ps[0:3, device_idx]
    #         test_point_in_tracker_space = (
    #             M_device_to_tracker[:3, :3] @ device_test_point
    #             + M_device_to_tracker[0:3, 3]
    #         )
    #         dp = test_point_in_tracker_space - tracker_point
    #         # TODO: error is not really fully error, there is supposed to be a constant distance
    #         # between tracker and device pose in real-world coords.
    #         # Perhaps we should be comparing to the mean? (variance)
    #         # However, seems useful to minimize.
    #         error = np.linalg.norm(dp)
    #         errors.append(error)
    #     return np.mean(errors), M_device_to_tracker

    # # Try different sync candidates, pick one that minimizes average distance from
    # # transformed device position to the tracker position.
    # # Currently for the transform we just try some pairs of tracker and device poses,
    # # and calculate M directly from that (instead of some global optimization that would
    # # minimize total error when considering the whole trajectories).
    # errors_per_sync = []
    # M_per_sync = []
    # sync_candidates = np.linspace(-20.0, 20.0, 1001)
    # # TODO more intelligent picking
    # N_candidates = [math.floor(i * 0.2 * tracker.ts.shape[0]) for i in range(1, 5)]
    # # print('N_candidates:', N_candidates)
    # for sync in sync_candidates:
    #     sync_errors_for_N = []
    #     Ms_for_N = []
    #     for N in N_candidates:
    #         mean_error, M = sync_errors(sync, N)
    #         sync_errors_for_N.append(mean_error)
    #         Ms_for_N.append(M)
    #     best_N_index = np.argmin(sync_errors_for_N)
    #     errors_per_sync.append(sync_errors_for_N[best_N_index])
    #     M_per_sync.append(Ms_for_N[best_N_index])
    # best_sync = sync_candidates[np.argmin(errors_per_sync)]
    # best_M = M_per_sync[np.argmin(errors_per_sync)]
    # # print('Optimal sync error:', min(errors_per_sync))

    best_sync=0.0

    return best_sync


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
    parser.add_argument(
        "--plot",
        dest="plot",
        help="Plot syncs for manual validation of results",
        action='store_true'
    )
    args = parser.parse_args()
    with open(args.tracker_input, "r") as f:
        tracker = load_tracker_data(f)
    with open(args.device_input, "r") as f:
        vio = load_poses(f, args.pose_name)

    syncs = [
        sync_movement_speeds(vio.t, vio.p, tracker.t, tracker.p),
        sync_rotation_diffs(vio.t, vio.r, tracker.t, tracker.r),
        sync_rotation_speeds(vio.t, vio.r, tracker.t, tracker.r),
    ]
    print("syncs:", syncs)

    if args.plot:

        import matplotlib.pyplot as plt

        # TODO: see plot code from align_trajectories.py
        # and plot_device_and_tracker.py

        fig, axs = plt.subplots(4, 1, constrained_layout=True)

        def plot(ax, method_name, sync):
            ax.set_title("sync = {:.2f}s".format(sync))
            ax.set_xlabel('time (s)')
            ax.set_ylabel('speed (m/s)'.format(sync))
            ax.legend()

        method_names = [
            'Sync movement speeds',
            'Sync rotation diff',
            'Sync rotation speeds',
        ]

        for ax, sync, method_name in zip(axs[1:], syncs, method_names):
            v_tracker = movement_speeds(tracker.t, tracker.p)
            synced_vio_times = vio.t + sync
            v_vio = movement_speeds(synced_vio_times, vio.p)
            print('shapes', vio.t.shape, v_vio.shape)
            ax.plot(tracker.t[:-2], v_tracker, "-", color="r", label='Tracker')
            ax.plot(vio.t[:-2], v_vio, "-", color="g", label='VIO device')
            plot(ax, method_name, sync)


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
