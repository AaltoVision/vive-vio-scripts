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
    # rs = []
    f = sys.stdin if args.input is None else open(args.input, "r")
    for line in f:
        j = json.loads(line)
        ts.append(j["time"])
        xs.append(j["position"]["x"])
        ys.append(j["position"]["y"])
        zs.append(j["position"]["z"])
    if f is not sys.stdin:
        f.close()

    # downsample
    sample_rate = int(args.sample_rate)
    ts = np.array([ts[i * sample_rate] for i in range(len(ts) // sample_rate)])
    xs = np.array([xs[i * sample_rate] for i in range(len(xs) // sample_rate)])
    ys = np.array([ys[i * sample_rate] for i in range(len(ys) // sample_rate)])
    zs = np.array([zs[i * sample_rate] for i in range(len(zs) // sample_rate)])
    # todo use numpy downsample some function

    fig = plt.figure()
    ax = Axes3D(fig)

    axis_min = min(min(xs), min(ys), min(zs))
    axis_max = max(max(xs), max(ys), max(zs))
    ax.set(
        xlim=(axis_min, axis_max), ylim=(axis_min, axis_max), zlim=(axis_min, axis_max)
    )

    line = ax.plot(xs, ys, zs, linestyle="-", marker="")[0]
    title = ax.set_title("Tracker position at t=0")
    fps = 60.0
    framerate = 1.0 / fps
    frames = fps * ts[-1]

    def update_graph(frame):
        frame = frame%frames
        expected_t = frame * framerate
        t = np.argmax(expected_t < ts)
        # print('exp t {}, t {}'.format(expected_t, t))
        line.set_data([xs[:t], ys[:t]])
        line.set_3d_properties(zs[:t])
        title.set_text("Tracker position at t={}".format(ts[t]))
        return title, line

    from matplotlib.animation import FuncAnimation
    # anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)
    anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)

    plt.show()
