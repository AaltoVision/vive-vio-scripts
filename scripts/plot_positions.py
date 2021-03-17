import argparse
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        dest="input",
        help="Input file with position data (stdin if not given)",
    )
    parser.add_argument(
        "-s",
        "--sample-rate",
        dest="sample_rate",
        help="How many samples to skip between samples (since input can be very high-res)",
    )
    args = parser.parse_args()
    ts = []
    xs = []
    ys = []
    zs = []
    frame_xs = []
    frame_ys = []
    frame_zs = []
    f = sys.stdin if args.input is None else open(args.input, "r")
    for line in f:
        j = json.loads(line)
        ts.append(j["time"])
        xs.append(j["position"]["x"])
        ys.append(j["position"]["y"])
        zs.append(j["position"]["z"])
        if "rotation" in j:
            frame_xs.append(np.array(j["rotation"]["col0"]))
            frame_ys.append(np.array(j["rotation"]["col1"]))
            frame_zs.append(np.array(j["rotation"]["col2"]))
    if f is not sys.stdin:
        f.close()

    # downsample (note: much faster to use sample_rate=1 and downsample data beforehand)
    sample_rate = int(args.sample_rate)
    ts = np.array(ts[::sample_rate])
    xs = np.array(xs[::sample_rate])
    ys = np.array(ys[::sample_rate])
    zs = np.array(zs[::sample_rate])
    frame_xs = np.array(frame_xs[::sample_rate])
    frame_ys = np.array(frame_ys[::sample_rate])
    frame_zs = np.array(frame_zs[::sample_rate])

    fig = plt.figure()
    ax = Axes3D(fig)

    # TODO: center on the interesting part
    axis_min = min(min(xs), min(ys), min(zs))
    axis_max = max(max(xs), max(ys), max(zs))
    # axis_min = min(min(xs), min(ys), min(zs)) * 0.5
    # axis_max = max(max(xs), max(ys), max(zs)) * 0.5
    ax.set(
        xlim=(axis_min, axis_max), ylim=(axis_min, axis_max), zlim=(axis_min, axis_max)
    )

    line = ax.plot(xs, ys, zs, linestyle="-", marker="")[0]
    title = ax.set_title("Tracker position at t=0")
    fps = 60.0
    framerate = 1.0 / fps
    frames = fps * ts[-1]

    def update_graph(frame):
        frame = frame % frames
        expected_t = frame * framerate
        t = np.argmax(expected_t < ts)
        line.set_data([xs[:t], ys[:t]])
        line.set_3d_properties(zs[:t])

        def draw_quivers(vs, color, quiver_rate):
            ax.quiver(
                xs[::quiver_rate],
                ys[::quiver_rate],
                zs[::quiver_rate],
                vs[:, 0][::quiver_rate],
                vs[:, 1][::quiver_rate],
                vs[:, 2][::quiver_rate],
                color=color,
                length=(axis_max - axis_min) * 0.03,
            )

        if len(frame_xs) > 0:
            draw_quivers(frame_xs, 'r', 30)
            draw_quivers(frame_ys, 'g', 30)
            draw_quivers(frame_zs, 'b', 30)
        title.set_text("Tracker position at t={}".format(ts[t]))
        return title, line

    from matplotlib.animation import FuncAnimation

    # anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)
    anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)

    plt.show()
