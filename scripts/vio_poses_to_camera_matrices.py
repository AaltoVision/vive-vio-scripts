import sys
import json
import numpy as np

# q is quaternion with elements (x, y, z, w)
def quat2rmat(q: np.array):
    return np.array(
        [
            [
                q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3],
                2 * q[1] * q[2] - 2 * q[0] * q[3],
                2 * q[1] * q[3] + 2 * q[0] * q[2],
            ],
            [
                2 * q[1] * q[2] + 2 * q[0] * q[3],
                q[0] * q[0] - q[1] * q[1] + q[2] * q[2] - q[3] * q[3],
                2 * q[2] * q[3] - 2 * q[0] * q[1],
            ],
            [
                2 * q[1] * q[3] - 2 * q[0] * q[2],
                2 * q[2] * q[3] + 2 * q[0] * q[1],
                q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3],
            ],
        ]
    )


# Quick tool for recovering the camera pose matrix from VIO data.
# In VIO data, it is stored as orientation=R, position=-R.t() * p
# Therefore view matrix is (R, -Rp), and camera matrix is inverse of that
if __name__ == "__main__":
    for line in sys.stdin:
        j = json.loads(line)
        if "position" in j and "orientation" in j:
            p = np.array(
                [
                    [
                        j["position"]["x"],
                    ],
                    [
                        j["position"]["y"],
                    ],
                    [
                        j["position"]["z"],
                    ],
                ]
            )
            q = np.array(
                [
                    j["orientation"]["x"],
                    j["orientation"]["y"],
                    j["orientation"]["z"],
                    j["orientation"]["w"],
                ]
            )
            R = quat2rmat(q)

            # Recover original view matrix
            V = np.identity(4)
            V[:3, :3] = R
            V[:3, 3:4] = -R @ p

            # Recover camera matrix from view matrix
            C = np.linalg.inv(V)

            del j["orientation"]
            j["position"] = {
                "x": C[0, 3],
                "y": C[1, 3],
                "z": C[2, 3],
            }
            j["rotation"] = {
                "col0": [v for v in C[:3, 0]],
                "col1": [v for v in C[:3, 1]],
                "col2": [v for v in C[:3, 2]],
            }
            print(json.dumps(j))
        else:
            print(line)
