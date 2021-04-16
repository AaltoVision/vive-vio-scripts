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
        p = np.array(
            [
                [
                    j["cameraExtrinsics"]["position"]["x"],
                ],
                [
                    j["cameraExtrinsics"]["position"]["y"],
                ],
                [
                    j["cameraExtrinsics"]["position"]["z"],
                ],
            ]
        )
        q = np.array(
            [
                j["cameraExtrinsics"]["orientation"]["x"],
                j["cameraExtrinsics"]["orientation"]["y"],
                j["cameraExtrinsics"]["orientation"]["z"],
                j["cameraExtrinsics"]["orientation"]["w"],
            ]
        )
        R = quat2rmat(q)

        # Recover original view matrix
        V = np.identity(4)
        V[:3, :3] = R
        V[:3, 3:4] = -R @ p

        # Recover camera matrix from view matrix
        C = np.linalg.inv(V)

        j["VIO_pose"] = [
            [ C[0, 0], C[0, 1], C[0, 2], C[0, 3] ],
            [ C[1, 0], C[1, 1], C[1, 2], C[1, 3] ],
            [ C[2, 0], C[2, 1], C[2, 2], C[2, 3] ],
        ]

        print(json.dumps(j))
