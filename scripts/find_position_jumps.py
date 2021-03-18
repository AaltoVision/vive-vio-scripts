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

    # print jumps
    for i, t, d in zip(range(len(ts)), ts[:-1], ds):
        if d > 0.3:
            print('At t={}, jump of {:.2f}m'.format(t, d))
            print('    ps[{}]: {}'.format(i, ps[i]))
            print('    ps[{}]: {}'.format(i+1, ps[i+1]))
            if (ps[i] == np.array([0.0, 0.0, 0.0])).all():
                print('    delete until {0} (including {0})'.format(i))
            if (ps[i+1] == np.array([0.0, 0.0, 0.0])).all():
                print('    delete from', i+1)
