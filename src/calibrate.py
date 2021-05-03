import numpy as np

# Note: Calibration is not finished. This python version is based on libs/calibrate_vio_tracker/src/main.cpp, which also is not finished and probably has some math bug. Basic derivation of the math is in docs/calibration_math.jpg, but may have some error. In that image, 'R_vio(i)' and 't_VIO' are orientation and position of the VIO device in the Apriltag's local (real-world) coordinates at frame 'i', which is what the 'find_tag_space_poses' program outputs.

# Find calibration matrix (tracker position in VIO local coords)
# TODO: currently just returns the position, not relative orientation (tracker orientation in VIO local coords),
# however that should be solvable from just one tracker-VIO pose correspondence
def calibrate_from_two_frames(R_tag, dR_vio, dT_vio, dT_tracker):
    """
    Calibrate from just two frames of pose data
    TODO: think math is correct, but could not get working yet
    """
    x = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio)
    return x

"""
R_tag: 3x3 Numpy array
    Rotation of the tag in the tracking space. This depends on how you have placed the tag in relation to the tracking space. See docs/calibration_tag_setup_example.jpg for example where R_tag should be
    R_tag = 
        [
            [ -1,  0,  0 ],
            [  0,  0,  1 ],
            [  0,  1,  0 ],
        ]
    Note that the base station should be the one that tracking space is related to.
    You can check this by testing near which base station the tracker position is reported as (0, 0, 0).
"""
def calibrate(R_tag, p_vio, R_vio, p_tracker, vio_to_tracker):
    """
    For now just calibrate from two frames, instead of global optimal
    """

    prev_vio = n_vio // 4
    next_vio = (n_vio * 3) // 4
    prev_tracker = vio_to_tracker[prev_vio]
    next_tracker = vio_to_tracker[next_vio]

    x = calibrate_from_two_frames(
        R_tag,
        R_vio[:, :, next_vio] - R_vio[:, :, prev_vio],
        p_vio[:, next_vio] - p_vio[:, prev_vio],
        p_tracker[:, next_tracker] - p_tracker[:, prev_tracker],
    )

    return x

def test_calibrate():
    pass
