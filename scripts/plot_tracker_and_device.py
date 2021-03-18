import argparse
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


class position_data:
    def __init__(self):
        # self.ts = np.array([])
        # self.xs = np.array([])
        # self.ys = np.array([])
        # self.zs = np.array([])
        # self.frame_xs = np.array([])
        # self.frame_ys = np.array([])
        # self.frame_zs = np.array([])
        self.ts = []
        self.xs = []
        self.ys = []
        self.zs = []
        self.frame_xs = []
        self.frame_ys = []
        self.frame_zs = []

def load_data(lines):
    data = position_data()
    for line in lines:
        j = json.loads(line)
        data.ts.append(j["time"])
        data.xs.append(j["position"]["x"])
        data.ys.append(j["position"]["y"])
        data.zs.append(j["position"]["z"])
        if "rotation" in j:
            data.frame_xs.append(np.array(j["rotation"]["col0"]))
            data.frame_ys.append(np.array(j["rotation"]["col1"]))
            data.frame_zs.append(np.array(j["rotation"]["col2"]))
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
    with open(args.tracker_input, 'r') as f:
        tracker = load_data(f)
    with open(args.device_input, 'r') as f:
        device = load_data(f)

    fig = plt.figure()
    ax = Axes3D(fig)

    def apply_transform(positions: position_data, M: np.array):
        ps = list(zip(positions.xs, positions.ys, positions.zs))
        for i in range(len(positions.xs)):
            Mp = M @ np.array(ps[i])
            # print('mp shape', Mp.shape)
            positions.xs[i] = Mp[0]
            positions.ys[i] = Mp[1]
            positions.zs[i] = Mp[2]
    
    # M = np.array([
    #     [1,0,0],
    #     [0,1,0],
    #     [0,0,1],
    #     ])
    M = np.array([
        [0,1,0],
        [1,0,0],
        [0,0,1],
        ])
    apply_transform(tracker, M)

    ax.plot(xs=tracker.xs, ys=tracker.ys, zs=tracker.zs, linestyle="-", marker="", color="r")
    ax.plot(xs=device.xs, ys=device.ys, zs=device.zs, linestyle="-", marker="", color="g")

    plt.show()

    # line = ax.plot(xs, ys, zs, linestyle="-", marker="")[0]
    # title = ax.set_title("Tracker position at t=0")
    # fps = 60.0
    # framerate = 1.0 / fps
    # frames = fps * ts[-1]

    # def update_graph(frame):
    #     frame = frame % frames
    #     expected_t = frame * framerate
    #     t = np.argmax(expected_t < ts)
    #     line.set_data([xs[:t], ys[:t]])
    #     line.set_3d_properties(zs[:t])

    #     def draw_quivers(vs, color, quiver_rate):
    #         ax.quiver(
    #             xs[::quiver_rate],
    #             ys[::quiver_rate],
    #             zs[::quiver_rate],
    #             vs[:, 0][::quiver_rate],
    #             vs[:, 1][::quiver_rate],
    #             vs[:, 2][::quiver_rate],
    #             color=color,
    #             length=(axis_max - axis_min) * 0.03,
    #         )

    #     if len(frame_xs) > 0:
    #         draw_quivers(frame_xs, "r", 30)
    #         draw_quivers(frame_ys, "g", 30)
    #         draw_quivers(frame_zs, "b", 30)
    #     title.set_text("Tracker position at t={}".format(ts[t]))
    #     return title, line

    # from matplotlib.animation import FuncAnimation

    # # anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)
    # anim = FuncAnimation(fig, update_graph, len(xs), interval=framerate, blit=True)

    # plt.show()
