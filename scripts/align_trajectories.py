# TODO

import argparse
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class pose_data:
    def __init__(self):
        self.ts = np.array(None)  # Time (seconds)
        self.ps = np.array(None)  # Positions (x,y,z)
        self.frame_xs = np.array(None)
        self.frame_ys = np.array(None)
        self.frame_zs = np.array(None)


def load_data(lines):
    lines = list(lines)
    n = len(lines)
    data = pose_data()
    data.ts = np.zeros(n)
    data.ps = np.zeros((3, n))
    data.frame_xs = np.zeros((3, n))
    data.frame_ys = np.zeros((3, n))
    data.frame_zs = np.zeros((3, n))
    for i, line in enumerate(lines):
        j = json.loads(line)
        data.ts[i] = j["time"]
        data.ps[:, i] = [
            j["position"]["x"],
            j["position"]["y"],
            j["position"]["z"],
        ]
        if "rotation" in j:
            data.frame_xs[:, i] = j["rotation"]["col0"]
            data.frame_ys[:, i] = j["rotation"]["col1"]
            data.frame_zs[:, i] = j["rotation"]["col2"]
    return data


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
        help="Input file with device position data",
        required=True,
    )
    args = parser.parse_args()
    with open(args.tracker_input, "r") as f:
        tracker = load_data(f)
    with open(args.device_input, "r") as f:
        device = load_data(f)

    # For now, we first align device data to start at 0, since tracker data does.
    # However, tracker data will have real timestamps later, that should be similar to device timestamps,
    # so that should actually be good info to keep and use almost directly (maybe small fine-tuning time sync still,
    # since clocks are probably a little bit different)

    tracker.ts -= tracker.ts[0]
    device.ts -= device.ts[0]

    # def plot_distances_and_time_sync(tracker, device):

    # timesync: maybe just cosine similarity, or something (minus mean, normalize, then dot)

    tracker_ds = np.linalg.norm(
        tracker.ps[:, 1:-1] - tracker.ps[:, 0:-2], axis=0, keepdims=True
    )
    device_ds = np.linalg.norm(
        device.ps[:, 1:-1] - device.ps[:, 0:-2], axis=0, keepdims=True
    )

    # Find M from 100th frame ( TODO: time sync first! and not nth data, but sample at 't'...)
    M_tracker = np.identity(4)
    M_tracker[0:3, 3] = tracker.ps[0:3, 100]
    M_tracker[:3, 0] = tracker.frame_xs[:3, 100]
    M_tracker[:3, 1] = tracker.frame_ys[:3, 100]
    M_tracker[:3, 2] = tracker.frame_zs[:3, 100]
    # print(M_tracker)

    sync_device_to_tracker = 0.9 # device timestamps are 0.8s ahead of tracker timestamps

    def tracker_idx_to_device_idx(n):
        t = tracker.ts[n]
        return np.argmin( (device.ts + sync_device_to_tracker) < t )

    corresponding_device_N = tracker_idx_to_device_idx(100)
    print('corresponding_device_N', corresponding_device_N)
    M_device = np.identity(4)
    M_device[0:3, 3] = device.ps[0:3, corresponding_device_N]
    M_device[:3, 0] = device.frame_xs[:3, corresponding_device_N]
    M_device[:3, 1] = device.frame_ys[:3, corresponding_device_N]
    M_device[:3, 2] = device.frame_zs[:3, corresponding_device_N]
    # print(M_device)
    # NOTE ds should be scaled by (ts[n] - ts[n-1]), since sampling freq is different

    # Transform M
    def transform_points(points: np.array, M: np.array):
        n_points = points.shape[1]
        points_h = np.concatenate((points, np.ones((1, n_points))))
        transformed_points_h = M @ points_h
        points[:, :] = transformed_points_h[:3, :]

    M_device_to_tracker = M_tracker @ np.linalg.inv(M_device)
    errors = []
    transform_test_indices = [ 10*x for x in range(100) ] 
    for tracker_idx in transform_test_indices:
        device_idx = tracker_idx_to_device_idx(tracker_idx)
        print('--- test N={}'.format(tracker_idx))
        tracker_point = tracker.ps[0:3, tracker_idx]
        print('    Tracker point:', tracker_point)
        device_test_point = device.ps[0:3, device_idx]
        test_point_in_tracker_space = M_device_to_tracker[:3, :3] @ device_test_point + M_device_to_tracker[0:3, 3]
        print('    Transformed device point:', test_point_in_tracker_space)
        dp = test_point_in_tracker_space - tracker_point
        error = np.linalg.norm(dp)
        print('    |dp|:', error)
        errors.append(error)
    print('Total error:', sum(errors))

    # Plot
    fig, axs = plt.subplots(4, 1, constrained_layout=True)

    def plot_distances_by_time(
        ax, tracker_ds, device_ds, tracker_ts=None, device_ts=None
    ):
        tracker_ts = (
            tracker_ts if tracker_ts is not None else range(tracker_ds.shape[1])
        )
        device_ts = device_ts if device_ts is not None else range(device_ds.shape[1])
        ax.plot(tracker_ts, tracker_ds[0, :], "-", color="r", label='Tracker')
        ax.plot(device_ts, device_ds[0, :], "-", color="g", label='Device')

    # Original distances
    plot_distances_by_time(
        axs[0], tracker_ds, device_ds, tracker.ts[:-2], device.ts[:-2]
    )

    # Distances scaled by dt
    tracker_dts = tracker.ts[1:-1] - tracker.ts[0:-2]
    device_dts = device.ts[1:-1] - device.ts[0:-2]
    assert((tracker_dts > 0.0).all())
    assert((device_dts > 0.0).all())
    plot_distances_by_time(
        axs[1],
        tracker_ds / tracker_dts,
        device_ds / device_dts,
        tracker.ts[:-2],
        device.ts[:-2],
    )

    # Distances scaled by dt, time sync version
    synced_device_ts = device.ts + sync_device_to_tracker
    tracker_dts = tracker.ts[1:-1] - tracker.ts[0:-2]
    synced_device_dts = synced_device_ts[1:-1] - synced_device_ts[0:-2]
    plot_distances_by_time(
        axs[2],
        tracker_ds / tracker_dts,
        device_ds / synced_device_dts,
        tracker.ts[:-2],
        synced_device_ts[:-2],
    )

    axs[3].plot(transform_test_indices, errors)

    axs[0].set_title(r"$|\delta p|$")
    axs[1].set_title(r"$|\delta p| / \delta t$")
    axs[2].set_title(r"$|\delta p| / \delta t$, updated time sync {}s".format(sync_device_to_tracker))
    axs[3].set_title(r"transform errors, total={:.3f}".format(sum(errors)))
    axs[0].legend()
    axs[1].legend()
    axs[2].legend()
    axs[3].legend()

    plt.show()

    # def sample_indices(timestamps: np.ndarray, time_between_samples: float):
    #     indices = []
    #     target_t = timestamps[0]
    #     for i, t in enumerate(timestamps):
    #         while t >= target_t:
    #             indices.append(i)
    #             target_t += time_between_samples
    #     return indices

    # fps = 60
    # idx_tracker = sample_indices(tracker.ts, 1./fps)
    # print('idx tracker:', len(idx_tracker))
    # idx_device = sample_indices(device.ts, 1./fps)
    # print('idx tracker:', len(idx_device))
