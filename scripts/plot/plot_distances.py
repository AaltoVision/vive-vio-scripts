import argparse
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', dest='input', help='Input file with position data (stdin if not given)')
    args = parser.parse_args()
    ts = []
    xs = []
    ys = []
    zs = []
    f = sys.stdin if args.input is None else open(args.input, 'r')
    for line in f:
        j = json.loads(line)
        ts.append(j["time"])
        xs.append(j["position"]["x"])
        ys.append(j["position"]["y"])
        zs.append(j["position"]["z"])
    if f is not sys.stdin:
        f.close()

    # plot distances between p(t) and p(t+1) for each frame
    ps = [ np.array([x,y,z]) for (x,y,z) in zip(xs, ys, zs) ]
    ds = [ np.linalg.norm(ps[i] - ps[i+1]) for i in range(len(xs)-1) ]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    # ax.plot(range(1, len(ps)), ds, '.')
    ax.plot(ts[:-1], ds, '.')
    plt.xlabel("time (s)")
    plt.ylabel("distance (m)")

    plt.show()
