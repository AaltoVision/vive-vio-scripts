import argparse
import sys
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class position_data:
    def __init__(self):
        self.ts = np.array(None)
        self.xs = np.array(None)
        self.ys = np.array(None)
        self.zs = np.array(None)
        self.frame_xs = np.array(None)
        self.frame_ys = np.array(None)
        self.frame_zs = np.array(None)


def load_data(lines):
    lines = list(lines)
    n = len(lines)
    data = position_data()
    data.ts = np.zeros(n)
    data.xs = np.zeros(n)
    data.ys = np.zeros(n)
    data.zs = np.zeros(n)
    data.frame_xs = np.zeros((3, len(lines)))
    data.frame_ys = np.zeros((3, len(lines)))
    data.frame_zs = np.zeros((3, len(lines)))
    for i, line in enumerate(lines):
        j = json.loads(line)
        data.ts[i] = j["time"]
        data.xs[i] = j["position"]["x"]
        data.ys[i] = j["position"]["y"]
        data.zs[i] = j["position"]["z"]
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
    )
    parser.add_argument(
        "-d",
        "--device_input",
        dest="device_input",
        help="Input file with device position data",
    )
    args = parser.parse_args()
    with open(args.tracker_input, "r") as f:
        tracker = load_data(f)
    with open(args.device_input, "r") as f:
        device = load_data(f)

    fig = plt.figure()
    ax = Axes3D(fig)

    def apply_transform(positions: position_data, M: np.array):
        ps = list(zip(positions.xs, positions.ys, positions.zs))
        for i in range(len(positions.xs)):
            Mp = M @ np.array([ps[i][0], ps[i][1], ps[i][2], 1.0])
            positions.xs[i] = Mp[0]
            positions.ys[i] = Mp[1]
            positions.zs[i] = Mp[2]

    M = np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
        ]
    )
    apply_transform(tracker, M)

    # For both tracker and VIO data, remove first point from all points,
    # so there is higher chance that the plots look similar.
    # Note: probably less important for VIO data, since it considers beginning
    # point as origin, while for tracker, origin is at one of the base stations,
    # if room setup has not been done.
    tracker_remove_first_pos = np.array(
        [
            [1, 0, 0, -tracker.xs[0]],
            [0, 1, 0, -tracker.ys[0]],
            [0, 0, 1, -tracker.zs[0]],
        ]
    )
    apply_transform(tracker, tracker_remove_first_pos)
    device_remove_first_pos = np.array(
        [
            [1, 0, 0, -device.xs[0]],
            [0, 1, 0, -device.ys[0]],
            [0, 0, 1, -device.zs[0]],
        ]
    )
    apply_transform(device, device_remove_first_pos)

    # Rotate the tracker data for better plot match (manually found)
    M = np.array(
        [
            [0, 0, -1, 0],
            [0, 1, 0, 0],
            [1, 0, 0, 0],
        ]
    )
    apply_transform(tracker, M)

    # Make both data start at time t=0
    tracker.ts = tracker.ts - tracker.ts[0]
    device.ts = device.ts - device.ts[0]

    axis_min = min(
        min(tracker.xs),
        min(tracker.ys),
        min(tracker.zs),
        min(device.xs),
        min(device.ys),
        min(device.zs),
    )
    axis_max = max(
        max(tracker.xs),
        max(tracker.ys),
        max(tracker.zs),
        max(device.xs),
        max(device.ys),
        max(device.zs),
    )
    ax.set(
        xlim=(axis_min, axis_max), ylim=(axis_min, axis_max), zlim=(axis_min, axis_max)
    )

    tracker_plot = ax.plot(
        xs=[],
        ys=[],
        zs=[],
        linestyle="-",
        marker="",
        color="r",
        label="Tracker position",
    )
    device_plot = ax.plot(
        xs=[],
        ys=[],
        zs=[],
        linestyle="-",
        marker="",
        color="g",
        label="VIO device position",
    )
    ax.plot(
        xs=[0.0],
        ys=[0.0],
        zs=[0.0],
        linestyle="",
        marker="o",
        color="b",
        label="Origin",
    )
    ax.legend()
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")

    title = ax.set_title("Positions at t=0.00s")

    def update_graph(frame):
        seconds_since_anim_start = time.time() - anim_start

        tracker_positions_until_now = np.where(tracker.ts < seconds_since_anim_start)
        tracker_plot[0].set_data(
            tracker.xs[tracker_positions_until_now],
            tracker.ys[tracker_positions_until_now],
        )
        tracker_plot[0].set_3d_properties(tracker.zs[tracker_positions_until_now])

        device_positions_until_now = np.where(device.ts < seconds_since_anim_start)
        device_plot[0].set_data(
            device.xs[device_positions_until_now], device.ys[device_positions_until_now]
        )
        device_plot[0].set_3d_properties(device.zs[device_positions_until_now])

        title_text = "Tracker position at t={:.2f}s".format(seconds_since_anim_start)
        title.set_text(title_text)
        ax.set_title(title_text)
        return tracker_plot[0], device_plot[0], title

    from matplotlib.animation import FuncAnimation

    anim = FuncAnimation(fig, update_graph, tracker.xs.shape[0], interval=15, blit=True)

    anim_start = time.time()
    plt.show()
