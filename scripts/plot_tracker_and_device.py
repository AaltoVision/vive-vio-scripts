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
    parser.add_argument(
        "-a",
        "--animate",
        dest="animate",
        help="Animate the plot by timestamps instead of showing whole data at once",
        action='store_true'
    )
    parser.add_argument(
        "--animation_speed",
        dest="animation_speed",
        help="Animation speed",
        type=float,
        default=1.0,
    )
    parser.add_argument(
        "--loop",
        dest="loop",
        help="Loop animation",
        action='store_true'
    )
    args = parser.parse_args()
    with open(args.tracker_input, "r") as f:
        tracker = load_data(f)
    with open(args.device_input, "r") as f:
        device = load_data(f)

    fig = plt.figure()
    ax = Axes3D(fig)

    def transform_points(points: np.array, M: np.array):
        n_points = points.shape[1]
        points_h = np.concatenate((points, np.ones((1, n_points))))
        transformed_points_h = M @ points_h
        points[:, :] = transformed_points_h[:3, :]

    # M = np.array(
    #     [
    #         [1, 0, 0, 0],
    #         [0, 1, 0, 0],
    #         [0, 0, 1, 0],
    #     ]
    # )
    # transform_points(tracker.ps, M)

    # # For both tracker and VIO data, remove first point from all points,
    # # so there is higher chance that the plots look similar.
    # # Note: probably less important for VIO data, since it considers beginning
    # # point as origin, while for tracker, origin is at one of the base stations,
    # # if room setup has not been done.
    # tracker_remove_first_pos = np.array(
    #     [
    #         [1, 0, 0, -tracker.ps[0, 0]],
    #         [0, 1, 0, -tracker.ps[1, 0]],
    #         [0, 0, 1, -tracker.ps[2, 0]],
    #     ]
    # )
    # transform_points(tracker.ps, tracker_remove_first_pos)
    # device_remove_first_pos = np.array(
    #     [
    #         [1, 0, 0, -device.ps[0, 0]],
    #         [0, 1, 0, -device.ps[1, 0]],
    #         [0, 0, 1, -device.ps[2, 0]],
    #     ]
    # )
    # transform_points(device.ps, device_remove_first_pos)

    # # Rotate the tracker data for better plot match (manually found)
    # M = np.array(
    #     [
    #         [0, 0, -1, 0],
    #         [0, 1, 0, 0],
    #         [1, 0, 0, 0],
    #     ]
    # )
    # transform_points(tracker.ps, M)

    # Make both data start at time t=0
    tracker.ts = tracker.ts - tracker.ts[0]
    device.ts = device.ts - device.ts[0]

    axis_min = min(
        tracker.ps.min(),
        device.ps.min(),
    )
    axis_max = max(
        tracker.ps.max(),
        device.ps.max(),
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
        # Time in seconds since animation start
        t = (time.time() - anim_start) * args.animation_speed

        last_data_timestamp = max(tracker.ts.max(), device.ts.max())
        if args.loop:
            t = t % last_data_timestamp
        else:
            # Stop time at end
            t = min(t, last_data_timestamp, device.ts.max())

        if not args.animate:
            t = last_data_timestamp

        tracker_positions_until_now = tracker.ps[:, np.where(tracker.ts < t)[0]]
        tracker_plot[0].set_data(
            tracker_positions_until_now[0, :],
            tracker_positions_until_now[1, :],
        )
        tracker_plot[0].set_3d_properties(
            tracker_positions_until_now[2, :],
        )

        device_positions_until_now = device.ps[:, np.where(device.ts < t)[0]]
        device_plot[0].set_data(
            device_positions_until_now[0, :],
            device_positions_until_now[1, :],
        )
        device_plot[0].set_3d_properties(
            device_positions_until_now[2, :],
        )

        title_text = "Tracker position at t={:.2f}s".format(t)
        title.set_text(title_text)
        ax.set_title(title_text)
        return tracker_plot[0], device_plot[0], title

    from matplotlib.animation import FuncAnimation

    # Plot tracker and VIO device trajectories as animation
    anim = FuncAnimation(fig, update_graph, interval=15, blit=True)
    anim_start = time.time()
    plt.show()
