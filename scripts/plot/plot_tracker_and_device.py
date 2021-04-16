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


# TODO: might not need to treat tracker input as a separate thing from VIO inputs
# (all are handled the same currently)
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
        action='append',
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
    devices = []
    for device_file in args.device_input:
        with open(device_file, "r") as f:
            devices.append(load_data(f))

    fig = plt.figure()
    ax = Axes3D(fig)

    axis_min = min(
        tracker.ps.min(),
        min([device.ps.min() for device in devices])
    )
    axis_max = max(
        tracker.ps.max(),
        max([device.ps.max() for device in devices])
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
        label=args.tracker_input,
    )
    device_plots = [ax.plot(
        xs=[],
        ys=[],
        zs=[],
        linestyle="-",
        marker="",
        label=filename,
    ) for filename in args.device_input]
    ax.plot(
        xs=[0.0],
        ys=[0.0],
        zs=[0.0],
        linestyle="",
        marker="o",
        label="Origin",
    )
    ax.legend()
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")

    title = ax.set_title("Positions at t=0.00s")

    # Note: timestamps may be negative
    first_data_timestamp = min(tracker.ts.min(), min([d.ts.min() for d in devices]))
    last_data_timestamp = max(tracker.ts.max(), max([d.ts.max() for d in devices]))
    total_animation_length = last_data_timestamp - first_data_timestamp

    def update_graph(frame):
        # Time in seconds since animation start
        t = (time.time() - anim_start) * args.animation_speed

        if args.loop:
            while t > last_data_timestamp:
                t -= total_animation_length
        else:
            # Stop time at end
            t = min(t, last_data_timestamp, last_data_timestamp)

        if not args.animate:
            t = last_data_timestamp

        tracker_positions_until_now = tracker.ps[:, np.where(tracker.ts <= t)[0]]
        tracker_plot[0].set_data(
            tracker_positions_until_now[0, :],
            tracker_positions_until_now[1, :],
        )
        tracker_plot[0].set_3d_properties(
            tracker_positions_until_now[2, :],
        )

        for plot, device in zip(device_plots, devices):
            device_positions_until_now = device.ps[:, np.where(device.ts <= t)[0]]
            plot[0].set_data(
                device_positions_until_now[0, :],
                device_positions_until_now[1, :],
            )
            plot[0].set_3d_properties(
                device_positions_until_now[2, :],
            )

        title_text = "Positions at t={:.2f}s".format(t)
        title.set_text(title_text)
        ax.set_title(title_text)
        return tracker_plot[0], *[plot[0] for plot in device_plots], title

    from matplotlib.animation import FuncAnimation

    # Plot tracker and VIO device trajectories as animation
    anim = FuncAnimation(fig, update_graph, interval=15, blit=True)
    anim_start = time.time()
    plt.show()

    # import math
    # import matplotlib.animation as animation
    # Writer = animation.writers['ffmpeg']
    # writer = Writer(fps=15, metadata=dict(artist='Me'), bitrate=1800)
    # frames = int(math.ceil(total_animation_length * 1.0 / 0.015))
    # anim = FuncAnimation(fig, update_graph, frames, interval=15, blit=True)
    # anim_start = time.time()
    # anim.save('results/trajectory{}.mp4'.format(int(time.time())), writer=writer)