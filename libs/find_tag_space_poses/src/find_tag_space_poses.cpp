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

mat4 find_tag_space_pose(mat3x4 const& P, mat2x4 const& Y, mat4 const& Z)
{
    auto cv_Z = std::vector<cv::Point3d>{
        cv::Point3d{ Z(0, 0), Z(1, 0), Z(2, 0) },
        cv::Point3d{ Z(0, 1), Z(1, 1), Z(2, 1) },
        cv::Point3d{ Z(0, 2), Z(1, 2), Z(2, 2) },
        cv::Point3d{ Z(0, 3), Z(1, 3), Z(2, 3) },
    };
    auto cv_Y = std::vector<cv::Point2d>{
        cv::Point2d{ Y(0, 0), Y(1, 0) }, // bottom-left
        cv::Point2d{ Y(0, 1), Y(1, 1) }, // bottom-right
        cv::Point2d{ Y(0, 2), Y(1, 2) }, // top-right
        cv::Point2d{ Y(0, 3), Y(1, 3) }, // top-left
    };
    cv::Matx33d K = {
        P(0, 0), P(0, 1), P(0, 2),
        P(1, 0), P(1, 1), P(1, 2),
        P(2, 0), P(2, 1), P(2, 2),
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
    return C;
}

// Input in jsonl format (file or stdin) (file not supported currently):
//
//      {
//          "framePath": "/path/to/frames/123.png",
//          "cameraIntrinsics": {focal lengths, principal point...},
//          ... (any other elements, which are not used)
//      }
//
// Output is same data but with added 'tag_space_pose' 3x4 matrix (as a list of rows)
int main(int argc, char* argv[])
{
    auto input_file_option = std::string{};
    auto output_file_option = std::string{};
    auto tag_side_length = 0.0;

    cxxopts::Options options(argv[0], "");
    options.add_options()
        ("i,input", "Path to the VIO input file", cxxopts::value(input_file_option))
        ("o,output", "Path to the output file", cxxopts::value(output_file_option))
        ("s,tag_side_length", "Length of the tag's sides in meters in the input images", cxxopts::value(tag_side_length))
        ;

    auto parsed_args = options.parse(argc, argv);
    if (parsed_args.count("help"))
    {
        std::cout << options.help() << std::endl;
        return 0;
    }

    auto arg_missing = [&](const char* arg_name)
    {
        if (parsed_args.count(arg_name) == 0)
        {
            std::fprintf(stderr, "Missing argument: %s.\n", arg_name);
            std::cerr << options.help() << std::endl;
            std::cerr << "See README.md for more instructions." << std::endl;
            return true;
        }
        return false;
    };

    if (arg_missing("input")) return 1;
    if (arg_missing("output")) return 1;
    if (arg_missing("tag_side_length")) return 1;

    std::ifstream input(input_file_option);
    std::ofstream output(output_file_option);

    auto s = tag_side_length;
    mat4 Z;
    Z.col(0) = vec4{ -s/2, -s/2, 0, 1, }; // bottom-left
    Z.col(1) = vec4{ s/2, -s/2, 0, 1, }; // bottom-right
    Z.col(2) = vec4{ s/2, s/2, 0, 1, }; // top-right
    Z.col(3) = vec4{ -s/2, s/2, 0, 1, }; // top-left

    // This is constant, tag is placed on top of base station in expected way
    mat4 tag_orientation_in_tracking_space = mat4::Identity();
    tag_orientation_in_tracking_space.col(0) = vec4{ -1, 0, 0, 0 };
    tag_orientation_in_tracking_space.col(1) = vec4{ 0, 0, 1, 0 };
    tag_orientation_in_tracking_space.col(2) = vec4{ 0, 1, 0, 0 };

    // Read in VIO data, and solve VIO device position in tracking space from Apriltag in frame
    std::string line;
    while (std::getline(input, line))
    {
        auto j = json::parse(line);
        auto markers = j["markers"];

        // Note: no output if tag is not found or is ambiguous
        if (markers.size() == 1)
        {
            mat3x4 P;
            parse_camera_intrinsics(j["cameraIntrinsics"], P);

            mat2x4 cv_Y;
            auto const& d = markers[0];
            cv_Y << d[0][0], d[1][0], d[2][0], d[3][0],
                d[0][1], d[1][1], d[2][1], d[3][1];

            auto C = find_tag_space_pose(P, cv_Y, Z);

            j["tag_space_pose"] = {
                { C(0, 0), C(0, 1), C(0, 2), C(0, 3), },
                { C(1, 0), C(1, 1), C(1, 2), C(1, 3), },
                { C(2, 0), C(2, 1), C(2, 2), C(2, 3), },
            };

            output << j.dump() << "\n";

        }
    }
}
