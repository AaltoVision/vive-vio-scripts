#ifndef _USE_MATH_DEFINES
#define _USE_MATH_DEFINES
#endif
#include <cmath>

#ifndef NOMINMAX
#define NOMINMAX
#endif

#include <nlohmann/json.hpp>
#include <Eigen/Dense>
#include <cxxopts.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/imgproc/imgproc_c.h>
#include <opencv2/calib3d.hpp>
#include <fstream>
#include <iostream>
#include <iomanip>
#include <string>
#include <array>
#include <algorithm>
#include <exception>
#include <functional>

using json = nlohmann::json;

using mat2x4 = Eigen::Matrix<double, 2, 4>;
using mat3x4 = Eigen::Matrix<double, 3, 4>;
using mat3 = Eigen::Matrix3d;
using mat4 = Eigen::Matrix4d;
using vec2 = Eigen::Vector2d;
using vec3 = Eigen::Vector3d;
using vec4 = Eigen::Vector4d;

// Fixed-size Eigen types' allocation must be aligned
template<typename T>
using e_vec = std::vector<T, Eigen::aligned_allocator<T>>;

void parse_camera_intrinsics(json const &camera_intrinsics,
                             mat3x4& intrinsic_matrix)
{
    auto const focal_length_x = camera_intrinsics["focalLengthX"].get<float>();
    auto const focal_length_y = camera_intrinsics["focalLengthY"].get<float>();
    auto const principal_point_x = camera_intrinsics["principalPointX"].get<float>();
    auto const principal_point_y = camera_intrinsics["principalPointY"].get<float>();

    intrinsic_matrix = mat3x4::Zero();
    intrinsic_matrix(0, 0) = focal_length_x;
    intrinsic_matrix(1, 1) = focal_length_y;
    intrinsic_matrix(0, 2) = principal_point_x;
    intrinsic_matrix(1, 2) = principal_point_y;
    intrinsic_matrix(2, 2) = 1.0f;
}

e_vec<mat4> solve_homographies(e_vec<mat3x4> const& Ps, e_vec<mat2x4> const& Ys, mat4 const& Z)
{
    auto Cs = e_vec<mat4>{};
    auto cv_Z = std::vector<cv::Point3d>{
        cv::Point3d{ Z(0, 0), Z(1, 0), Z(2, 0) },
        cv::Point3d{ Z(0, 1), Z(1, 1), Z(2, 1) },
        cv::Point3d{ Z(0, 2), Z(1, 2), Z(2, 2) },
        cv::Point3d{ Z(0, 3), Z(1, 3), Z(2, 3) },
    };
    for (size_t i = 0; i < Ys.size(); ++i)
    {
        auto cv_Y = std::vector<cv::Point2d>{
            cv::Point2d{ Ys[i](0, 0), Ys[i](1, 0) }, // bottom-left
            cv::Point2d{ Ys[i](0, 1), Ys[i](1, 1) }, // bottom-right
            cv::Point2d{ Ys[i](0, 2), Ys[i](1, 2) }, // top-right
            cv::Point2d{ Ys[i](0, 3), Ys[i](1, 3) }, // top-left
        };
        cv::Matx33d K = {
            Ps[i](0, 0), Ps[i](0, 1), Ps[i](0, 2),
            Ps[i](1, 0), Ps[i](1, 1), Ps[i](1, 2),
            Ps[i](2, 0), Ps[i](2, 1), Ps[i](2, 2),
        };
        cv::Vec3d r;
        cv::Vec3d T;
        cv::solvePnP(cv_Z, cv_Y, K, cv::Vec4d{ 0, 0, 0, 0 }, r, T);
        cv::Matx33d R;
        cv::Rodrigues(r, R);
        mat4 C;
        C << R(0, 0), R(0, 1), R(0, 2), T(0),
            R(1, 0), R(1, 1), R(1, 2), T(1),
            R(2, 0), R(2, 1), R(2, 2), T(2),
            0, 0, 0, 1;
        Cs.push_back(C);
    }
    return Cs;
}

double angle_between_rotations(mat3 const& A, mat3 const& B)
{
    mat3 R = A * B.transpose();
    auto angle = std::acos((R.trace() - 1.0) / 2.0);
    return std::min(angle, 2.0*M_PI - angle);
}

double radians_to_degrees(double radians)
{
    return radians * 360.0 / (2.0 * M_PI);
}

bool find_sync_from_orientations(
    Eigen::VectorXd vio_ts, e_vec<mat3> const& vio_rs,
    Eigen::VectorXd tracker_ts, e_vec<mat3> const& tracker_rs,
    double& optimal_sync
    )
{
    auto n_vio = (int)vio_ts.size();
    auto n_tracker = (int)tracker_ts.size();
    // std::printf("n_vio: %d\nn_tracker: %d\n", (int)n_vio, (int)n_tracker);

    auto vio_length = vio_ts[n_vio-1] - vio_ts[0];
    auto tracker_length = tracker_ts[n_tracker-1] - tracker_ts[0];
    // std::printf("VIO length: %.2fs\n", vio_length);
    // std::printf("Tracker length: %.2fs\n", tracker_length);

    // Make both start at t=0
    vio_ts.array() -= vio_ts[0];
    tracker_ts.array() -= tracker_ts[0];
    
    if (vio_length >= tracker_length)
    {
        std::fprintf(stderr, "Error: VIO track should be shorter than tracker track\n");
        return false;
    }

    // Finding sync (time offset) between the VIO and tracker rotation data:
    // - sample tracker at vio_t+sync
    // - compute shortest angle between the VIO rotations and corresponding (according to sync) tracker rotations
    // - for correct sync, the angle should be almost exactly same throughout the track, therefore we find sync that minimizes deviation from mean

    auto max_sync = tracker_length - vio_length;
    // auto syncs = Eigen::ArrayXd::LinSpaced(n_vio, 0.0, max_sync);
    auto syncs = Eigen::ArrayXd::LinSpaced((int)std::ceil(max_sync / 0.1)+1, 0.0, max_sync);

    Eigen::ArrayXd angles = Eigen::ArrayXd(n_vio);
    auto min_variance = 999999.0;
    auto min_variance_index = 0;
    for (auto i_sync = 0; i_sync < syncs.size(); ++i_sync)
    {
        auto i_tracker = 0;
        for (auto i_vio = 0; i_vio < n_vio; ++i_vio)
        {
            // Add sync to VIO timestamp; larger sync means later starting time for VIO track
            auto vio_t = vio_ts[i_vio] + syncs[i_sync];
            // Seek to first tracker timestamp that is greater-or-equal-to VIO timestamp
            while ( (tracker_ts[i_tracker] < vio_t) && (i_tracker < n_tracker-1) )
            {
                ++i_tracker;
            }
            angles[i_vio] = radians_to_degrees(
                angle_between_rotations(vio_rs[i_vio], tracker_rs[i_tracker]));
        }
        auto angle_mean = angles.mean();
        auto angle_variance = (1. / n_vio) * (angles - angle_mean).square().sum();
        // std::printf("sync=%.2f, angle_mean=%.4f, angle_variance=%.4f\n",
        //             syncs[i_sync], angle_mean, angle_variance);
        if (angle_variance < min_variance)
        {
            min_variance = angle_variance;
            min_variance_index = i_sync;
        }
    }

    optimal_sync = syncs[min_variance_index];

    return true;
}

auto map_vio_to_tracker_with_sync = [](auto const& vio_ts, auto const& tracker_ts, double sync, auto& map_vio_to_tracker)
{
    auto n_vio = (int)vio_ts.size();
    auto n_tracker = (int)tracker_ts.size();

    // Map VIO indices to tracker indices using this sync
    // auto map_vio_to_tracker = std::vector<int>(n_vio);
    auto i_tracker = 0;
    for (auto i_vio = 0; i_vio < n_vio; ++i_vio)
    {
        auto vio_t = vio_ts[i_vio] + sync;
        while ( (tracker_ts[i_tracker] < vio_t) && (i_tracker < n_tracker-1) )
        {
            ++i_tracker;
        }
        map_vio_to_tracker[i_vio] = i_tracker;
    }
    // return map_vio_to_tracker;
};

bool find_sync_from_angular_speeds(
    Eigen::ArrayXd vio_ts, Eigen::ArrayXd vio_vs,
    Eigen::ArrayXd tracker_ts, Eigen::ArrayXd tracker_vs,
    double& optimal_sync
    )
{
    auto n_vio = (int)vio_ts.size();
    auto n_tracker = (int)tracker_ts.size();
    // std::printf("n_vio: %d\nn_tracker: %d\n", (int)n_vio, (int)n_tracker);

    auto vio_length = vio_ts[n_vio-1] - vio_ts[0];
    auto tracker_length = tracker_ts[n_tracker-1] - tracker_ts[0];
    // std::printf("VIO length: %.2fs\n", vio_length);
    // std::printf("Tracker length: %.2fs\n", tracker_length);

    // Make both start at t=0
    vio_ts.array() -= vio_ts[0];
    tracker_ts.array() -= tracker_ts[0];
    
    if (vio_length >= tracker_length)
    {
        std::fprintf(stderr, "Error: VIO track should be shorter than tracker track\n");
        return false;
    }

    auto max_sync = tracker_length - vio_length;
    // auto syncs = Eigen::ArrayXd::LinSpaced(n_vio, 0.0, max_sync);
    auto syncs = Eigen::ArrayXd::LinSpaced((int)std::floor(max_sync / 0.1)+1, 0.0, max_sync);

    auto max_similarity = -999999.0;
    auto max_similarity_index = 0;
    auto map_vio_to_tracker = std::vector<int>(n_vio);
    for (auto i_sync = 0; i_sync < syncs.size(); ++i_sync)
    {
        // Map VIO indices to tracker indices using this sync
        auto i_tracker = 0;
        for (auto i_vio = 0; i_vio < n_vio; ++i_vio)
        {
            auto vio_t = vio_ts[i_vio] + syncs[i_sync];
            while ( (tracker_ts[i_tracker] < vio_t) && (i_tracker < n_tracker-1) )
            {
                ++i_tracker;
            }
            map_vio_to_tracker[i_vio] = i_tracker;
        }

        // Find corresponding tracker speeds
        Eigen::VectorXd matched_tracker_vs(n_vio-1);
        for (auto i_vio = 0; i_vio < n_vio-1; ++i_vio)
        {
            matched_tracker_vs[i_vio] = tracker_vs[map_vio_to_tracker[i_vio]];
        }

        // Use cosine similarity to evaluate how good match it is
        auto similarity = vio_vs.matrix().stableNormalized().dot(matched_tracker_vs.stableNormalized());

        // std::printf("sync=%.2f, similarity=%.4f\n", syncs[i_sync], similarity);
        if (similarity > max_similarity)
        {
            max_similarity = similarity;
            max_similarity_index = i_sync;
        }
    }

    optimal_sync = syncs[max_similarity_index];

    return true;
}

// Input in jsonl format (file or stdin) (file not supported currently):
//
//      {
//          "time": ...,
//          "framePath": "/path/to/frames/123.png",
//          "cameraIntrinsics": {focal lengths, principal point...},
//          "markers": [{"id":0,"corners":[[p0x,p0y],[p1x,p1y]...]}, {"id":1...}]
//          ... (any other elements, which are not used)
//      }
//
int main(int argc, char* argv[])
{
    auto vio_input_file_option = std::string{};
    auto tracker_input_file_option = std::string{};
    auto test=false;

    cxxopts::Options options(argv[0], "");
    options.add_options()
        ("vio", "Path to the VIO input file", cxxopts::value(vio_input_file_option))
        ("tracker", "Path to the tracker input file", cxxopts::value(tracker_input_file_option))
        ("test", "temp", cxxopts::value(test))
        ;

    auto parsed_args = options.parse(argc, argv);
    if (parsed_args.count("help"))
    {
        std::cout << options.help() << std::endl;
        return 0;
    }

    if (parsed_args.count("vio") == 0)
    {
        std::cerr << "Missing argument: input." << std::endl;
        std::cerr << options.help() << std::endl;
        std::cerr << "See README.md for more instructions." << std::endl;
        return 1;
    }
    std::ifstream vio_input(vio_input_file_option);

    if (parsed_args.count("tracker") == 0)
    {
        std::cerr << "Missing argument: tracker." << std::endl;
        std::cerr << options.help() << std::endl;
        std::cerr << "See README.md for more instructions." << std::endl;
        return 1;
    }
    std::ifstream tracker_input(tracker_input_file_option);


    // TODO: cli option
    auto const s = 0.025; // 2.5 cm
    mat4 Z;
    Z.col(0) = vec4{ -s/2, -s/2, 0, 1, }; // bottom-left
    Z.col(1) = vec4{ s/2, -s/2, 0, 1, }; // bottom-right
    Z.col(2) = vec4{ s/2, s/2, 0, 1, }; // top-right
    Z.col(3) = vec4{ -s/2, s/2, 0, 1, }; // top-left

    // This is constant, tag is placed on top of base station in expected way
    mat4 tag_orientation_in_tracking_space = mat4::Identity();
    tag_orientation_in_tracking_space.col(0) = vec4{ -1, 0, 0, 0 };
    tag_orientation_in_tracking_space.col(1) = vec4{ 0, 0, 1, 0 };
    // Let's say tag faces towards its own Z+ (so it is right-handed)
    tag_orientation_in_tracking_space.col(2) = vec4{ 0, 1, 0, 0 };
    // std::printf("tag_orientation_in_tracking_space:\n");
    // std::cout << tag_orientation_in_tracking_space << "\n";

    // Read in VIO data, and solve VIO device position in tracking space from Apriltag in frame
    auto vio_ts = std::vector<double>();
    auto vio_rs = e_vec<mat3>();
    auto vio_ps = e_vec<vec3>();
    std::string line;
    int total_input_frames = 0;
    while (std::getline(vio_input, line))
    {
        ++total_input_frames;
        auto j = json::parse(line);

        auto markers = j["markers"];

        if (markers.size() == 1)
        {
            mat3x4 P;
            parse_camera_intrinsics(j["cameraIntrinsics"], P);

            // Find 
            auto Ps = e_vec<mat3x4>();
            auto cv_Ys = e_vec<mat2x4>{};
            Ps.push_back(P);
            mat2x4 cv_Y;
            auto const& d = markers[0];
            cv_Y << d[0][0], d[1][0], d[2][0], d[3][0],
                d[0][1], d[1][1], d[2][1], d[3][1];
            cv_Ys.push_back(cv_Y);
            auto Cs = solve_homographies(Ps, cv_Ys, Z);
            auto C = Cs[0];

            // if (test)
            if (test && (total_input_frames - 1 == 61))
            {
                // std::printf("T[%d]: ", total_input_frames-1);
                // std::cout << C.col(3).head(3).transpose() << "\n";
                // std::cout << C.col(3).head(3).transpose() << "    " << j["framePath"] << "\n";
                std::cout << "--- " << "R[" << (total_input_frames-1) << "]: " << j["framePath"] << " ---\n";
                std::cout << C.topLeftCorner(3, 3) << "\n";
            }
            // mat3 fix_r = vec3{ 1, 1, 1 }.asDiagonal();
            // mat3 fix_r = vec3{ -1, -1, -1 }.asDiagonal();
            // mat3 fix_r = vec3{ -1, -1, 1 }.asDiagonal();
            // C.topLeftCorner(3, 3) = (fix_r * C.topLeftCorner(3, 3)).eval();

            vio_ts.push_back(j["time"]);
            vio_rs.push_back(C.topLeftCorner(3, 3)); // TODO: probably this rotation messing things up?
            vio_ps.push_back(C.col(3).head(3)); // This seemed to be good
        }
    }

    // Read in tracker data (timestamps and orientations)
    auto tracker_ts = std::vector<double>();
    auto tracker_ps = e_vec<vec3>();
    auto tracker_rs = e_vec<mat3>();
    {
        std::string line;
        while (std::getline(tracker_input, line))
        {
            auto j = json::parse(line);
            tracker_ts.push_back(j["time"]);
            mat3 R = mat3();
            auto x = j["rotation"]["col0"].get<std::vector<double>>();
            auto y = j["rotation"]["col1"].get<std::vector<double>>();
            auto z = j["rotation"]["col2"].get<std::vector<double>>();
            R.col(0) = vec3{ x[0], x[1], x[2] };
            R.col(1) = vec3{ y[0], y[1], y[2] };
            R.col(2) = vec3{ z[0], z[1], z[2] };
            tracker_rs.push_back(R);
            tracker_ps.push_back(vec3{ j["position"]["x"].get<double>(), j["position"]["y"].get<double>(), j["position"]["z"].get<double>() });
        }
    }

    // Find best matching sync, with rotation difference deviation from mean between tracks
    Eigen::Map<Eigen::VectorXd> eigen_vio_ts(vio_ts.data(), vio_ts.size());
    Eigen::Map<Eigen::VectorXd> eigen_tracker_ts(tracker_ts.data(), tracker_ts.size());

    // // Note: angle not necessarily intuitive, if it is along a diagonal vector
    double orientation_diff_optimal_sync = 0.0;
    find_sync_from_orientations(eigen_vio_ts, vio_rs, eigen_tracker_ts, tracker_rs, orientation_diff_optimal_sync);

    // Find best matching sync, using cosine similarity of rotation speeds
    // (Seems more robust)
    auto n_vio = (int)vio_ts.size();
    auto n_tracker = (int)tracker_ts.size();
    Eigen::ArrayXd vio_vs(n_vio-1);
    for (auto i = 0; i < n_vio-1; ++i)
    {
        auto delta_angle =
            radians_to_degrees(angle_between_rotations(vio_rs[i], vio_rs[i+1]));
        vio_vs[i] = delta_angle / (vio_ts[i+1] - vio_ts[i]);
    }
    Eigen::ArrayXd tracker_vs(n_tracker-1);
    for (auto i = 0; i < n_tracker-1; ++i)
    {
        auto delta_angle =
            radians_to_degrees(angle_between_rotations(tracker_rs[i], tracker_rs[i+1]));
        tracker_vs[i] = delta_angle / (tracker_ts[i+1] - tracker_ts[i]);
    }
    double angular_speed_optimal_sync = 0.0;
    find_sync_from_angular_speeds(eigen_vio_ts, vio_vs, eigen_tracker_ts, tracker_vs, angular_speed_optimal_sync);
    std::printf("Best sync from minimizing rotation difference deviation from mean: %.2f\n",
                orientation_diff_optimal_sync);
    std::printf("Best sync from angular speeds: %.2f\n", angular_speed_optimal_sync);

    // Find 'd' from successive datapoints
    {
        // auto optimal_sync = angular_speed_optimal_sync;
        auto optimal_sync = orientation_diff_optimal_sync;

        auto vio_ts_start0 = vio_ts;
        auto map_vio_ts = Eigen::Map<Eigen::ArrayXd>(vio_ts_start0.data(), n_vio);
        map_vio_ts -= vio_ts[0];
        auto tracker_ts_start0 = tracker_ts;
        auto map_tracker_ts = Eigen::Map<Eigen::ArrayXd>(tracker_ts_start0.data(), n_tracker);
        map_tracker_ts -= tracker_ts[0];

        auto vio_to_tracker = Eigen::ArrayXi(n_vio);
        // map_vio_to_tracker_with_sync(vio_ts, tracker_ts, optimal_sync, vio_to_tracker);

        map_vio_to_tracker_with_sync(map_vio_ts, map_tracker_ts, optimal_sync, vio_to_tracker);

        // std::cout << "Using sync " << optimal_sync << "\n";


        // Orientation of tag in tracking space (= relative to base station)
        mat3 R_tag;
        R_tag.col(0) = vec3{ -1,  0,  0 };
        R_tag.col(1) = vec3{  0,  0,  1 };
        R_tag.col(2) = vec3{  0,  1,  0 };

        auto R_vio = vio_rs; // tracking space orientation
        for (auto i = 0; i < n_vio; ++i)
        {
            R_vio[i] = (R_tag * R_vio[i]).eval();
        }

        // Does not seem to be working at all yet... maybe go through math one more time
        auto ds = Eigen::MatrixXd(3, n_vio-1);
        auto x_avg = vec3{ 0, 0, 0 };
        auto step = 10;
        auto i = 0;
        for (; step*(i+1) < n_vio; ++i)
        {
            auto i_prev = step*i;
            auto i_next = step*(i + 1);
            auto dT_tracker = tracker_ps[vio_to_tracker[i_next]] - tracker_ps[vio_to_tracker[i_prev]];
            auto dR_vio = R_vio[i_next] - R_vio[i_prev];
            auto dT_vio = vio_ps[i_next] - vio_ps[i_prev];
            // std::printf("dR_vio max: %.6f    dT_vio max: %.6f\n", dR_vio.maxCoeff(), dT_vio.maxCoeff());

            ds.col(i) = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio);
            // std::printf("x: %.4f, %.4f, %.4f\n", ds.col(i)[0], ds.col(i)[1], ds.col(i)[2]);

        }

        {
            auto i_prev = 0;
            auto i_next = n_vio - 1;
            auto dT_tracker = tracker_ps[vio_to_tracker[i_next]] - tracker_ps[vio_to_tracker[i_prev]];
            auto dR_vio = R_vio[i_next] - R_vio[i_prev];
            auto dT_vio = vio_ps[i_next] - vio_ps[i_prev];
            vec3 x = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio);
            std::printf("x(first,last), norm: %.4f, %.4f, %.4f,    %.4f\n", x[0], x[1], x[2], x.norm());
        }

        {
            auto i_prev = 0;
            auto i_next = n_vio / 2;
            auto dT_tracker = tracker_ps[vio_to_tracker[i_next]] - tracker_ps[vio_to_tracker[i_prev]];
            auto dR_vio = R_vio[i_next] - R_vio[i_prev];
            auto dT_vio = vio_ps[i_next] - vio_ps[i_prev];
            vec3 x = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio);
            std::printf("x(first,mid), norm: %.4f, %.4f, %.4f,    %.4f\n", x[0], x[1], x[2], x.norm());
        }

        {
            auto i_prev = n_vio / 2;
            auto i_next = n_vio - 1;
            auto dT_tracker = tracker_ps[vio_to_tracker[i_next]] - tracker_ps[vio_to_tracker[i_prev]];
            auto dR_vio = R_vio[i_next] - R_vio[i_prev];
            auto dT_vio = vio_ps[i_next] - vio_ps[i_prev];
            vec3 x = dR_vio.inverse() * (dT_tracker - R_tag * dT_vio);
            std::printf("x(mid,last), norm: %.4f, %.4f, %.4f,    %.4f\n", x[0], x[1], x[2], x.norm());
        }

    //     // TODO actual optimization
    }

    // TODO check if R_tag is correct, and opencv homography coordinate system (C's translation part mainly)

}


// Base station coordinate system:
// - Y+ points towards ceiling
// - Z- points towards tracking area
// - X+ points towards tag's X-

// Orientation of VIO device in tag space
// OpenCV coordinate system:
// -   x+ points right in image
// -   y+ points down in image
// -   z+ points away from camera ('into' the image)

// // Orientation of OpenCV frame in OpenGL-style coordinate system
// // OpenGL-style coordinate system:
// // -   x+ points right in image
// // -   y+ points up in image
// // -   z+ points away from image (towards camera)

