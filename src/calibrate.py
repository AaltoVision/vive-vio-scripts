# Find calibration matrix (tracker position in VIO local coords)

# auto i_prev = 0;
# auto i_next = n_vio - 1;
# auto dT_tracker = tracker_ps[vio_to_tracker[i_next]] - tracker_ps[vio_to_tracker[i_prev]];
# auto dR_vio = R_vio[i_next] - R_vio[i_prev];
# auto dT_vio = vio_ps[i_next] - vio_ps[i_prev];
# vec3 x = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio);
# std::printf("x(first,last), norm: %.4f, %.4f, %.4f,    %.4f\n", x[0], x[1], x[2], x.norm());

def calibrate():
    pass