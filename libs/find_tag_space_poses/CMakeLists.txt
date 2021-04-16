cmake_minimum_required(VERSION 3.5.0)
project(find_tag_space_poses)

# Compile options etc.
set(CMAKE_CXX_STANDARD 17)

# Find OpenCV package
find_package(OpenCV)

# dependency: nlohmann_json
option(JSON_BuildTests OFF)
add_subdirectory(libs/json)

# dependency: cxxopts
option(CXXOPTS_BUILD_EXAMPLES OFF)
option(CXXOPTS_BUILD_TESTS OFF)
option(CXXOPTS_ENABLE_INSTALL OFF)
add_subdirectory(libs/cxxopts)

# find_tag_space_poses
add_executable(find_tag_space_poses
    "src/find_tag_space_poses.cpp"
    )
target_include_directories(find_tag_space_poses PUBLIC "libs/eigen/")
target_link_libraries(find_tag_space_poses
    ${OpenCV_LIBS}
    nlohmann_json::nlohmann_json
    cxxopts)
target_compile_definitions(find_tag_space_poses PRIVATE _CRT_SECURE_NO_WARNINGS _SILENCE_CXX17_RESULT_OF_DEPRECATION_WARNING NOMINMAX _USE_MATH_DEFINES)

if (${CMAKE_VERSION} VERSION_GREATER_EQUAL "3.16.0")
    target_precompile_headers(find_tag_space_poses PRIVATE src/pch.h)
endif()
