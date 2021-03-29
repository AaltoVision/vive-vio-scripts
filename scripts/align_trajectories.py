# TODO

import argparse
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class position_data:
    def __init__(self):
        self.ts = np.array(None)  # Time (seconds)
        self.ps = np.array(None)  # Positions (x,y,z)
        self.frame_xs = np.array(None)
        self.frame_ys = np.array(None)
        self.frame_zs = np.array(None)


def load_data(lines):
    lines = list(lines)
    n = len(lines)
    data = position_data()
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

    # def plot_distances_by_time(tracker_ps, device_ps):
    def plot_distances_by_time(
        ax, tracker_ds, device_ds, tracker_ts=None, device_ts=None
    ):
        # ax.plot(range(tracker_ds.shape[1]), tracker_ds[0, :], "-", color="r")
        # ax.plot(range(device_ds.shape[1]), device_ds[0, :], "-", color="g")
        tracker_ts = (
            tracker_ts if tracker_ts is not None else range(tracker_ds.shape[1])
        )
        device_ts = device_ts if device_ts is not None else range(device_ds.shape[1])
        ax.plot(tracker_ts, tracker_ds[0, :], "-", color="r", label='Tracker')
        ax.plot(device_ts, device_ds[0, :], "-", color="g", label='Device')


    fig, axs = plt.subplots(3, 1, constrained_layout=True)

    tracker_ds = np.linalg.norm(
        tracker.ps[:, 1:-1] - tracker.ps[:, 0:-2], axis=0, keepdims=True
    )
    device_ds = np.linalg.norm(
        device.ps[:, 1:-1] - device.ps[:, 0:-2], axis=0, keepdims=True
    )

    # # Find M from 100th frame
    # print(tracker.ps.shape)
    # M_tracker = np.zeros((4, 4))
    # M_tracker[0:3, 3] = tracker.ps[0:3, 100]
    # M_tracker[:3, 0] = tracker.frame_xs[:3, 100]
    # M_tracker[:3, 1] = tracker.frame_ys[:3, 100]
    # M_tracker[:3, 2] = tracker.frame_zs[:3, 100]
    # print(M_tracker)
    # # NOTE ds should be scaled by (ts[n] - ts[n-1]), since sampling freq is different

    # # Transform M
    # def transform_points(points: np.array, M: np.array):
    #     n_points = points.shape[1]
    #     points_h = np.concatenate((points, np.ones((1, n_points))))
    #     transformed_points_h = M @ points_h
    #     points[:, :] = transformed_points_h[:3, :]

    # # Plot

    # Original distances
    plot_distances_by_time(
        axs[0], tracker_ds, device_ds, tracker.ts[:-2], device.ts[:-2]
    )

    # Distances scaled by dt
    tracker_dts = tracker.ts[1:-1] - tracker.ts[0:-2]
    device_dts = device.ts[1:-1] - device.ts[0:-2]
    print("min tracker dt:", tracker_dts.min())
    print("min device dt:", device_dts.min())
    plot_distances_by_time(
        axs[1],
        tracker_ds / tracker_dts,
        device_ds / device_dts,
        tracker.ts[:-2],
        device.ts[:-2],
    )

    # Distances scaled by dt, time sync version
    sync = 0.8
    synced_device_ts = device.ts + sync
    tracker_dts = tracker.ts[1:-1] - tracker.ts[0:-2]
    synced_device_dts = synced_device_ts[1:-1] - synced_device_ts[0:-2]
    plot_distances_by_time(
        axs[2],
        tracker_ds / tracker_dts,
        device_ds / synced_device_dts,
        tracker.ts[:-2],
        synced_device_ts[:-2],
    )


    # axs[0].set_title('Distance between current and previous position')
    # axs[1].set_title('Distance between current and previous position, divided by change in time')
    axs[0].set_title(r"$|\delta p|$")
    axs[1].set_title(r"$|\delta p| / \delta t$")
    axs[2].set_title(r"$|\delta p| / \delta t$, updated time sync {}s".format(sync))
    axs[0].legend()
    axs[1].legend()
    axs[2].legend()

    # # Zero mean
    # plot_distances_by_time(
    #     fig.add_subplot(grid + 2),
    #     tracker_ds - tracker_ds.mean(),
    #     device_ds - device_ds.mean(),
    # )

    # # Zero mean, unit variance
    # plot_distances_by_time(
    #     fig.add_subplot(grid + 3),
    #     (tracker_ds - tracker_ds.mean()) / tracker_ds.std(),
    #     (device_ds - device_ds.mean()) / device_ds.std(),
    # )

    # # Zero mean, unit variance, multiply 't'
    # plot_distances_by_time(
    #     fig.add_subplot(grid + 4),
    #     (tracker_ds - tracker_ds.mean()) / tracker_ds.std(),
    #     (device_ds - device_ds.mean()) / device_ds.std(),
    #     (tracker.ts[2:] - tracker.ts.mean()) / tracker.ts.std(),
    #     (device.ts[2:] - device.ts.mean()) / device.ts.std(),
    # )

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
