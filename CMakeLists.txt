# TODO: support Linux builds

cmake_minimum_required(VERSION 3.13.0)
project(ovr-tracker-app)

set(CMAKE_CXX_STANDARD 17)

set(EXTERNAL_LIBS "${CMAKE_SOURCE_DIR}/libs")

# dependency: openvr
# add_subdirectory("libs/openvr/src")
add_library(openvr_imported SHARED IMPORTED)
target_include_directories(openvr_imported INTERFACE
    "${EXTERNAL_LIBS}/openvr/headers/"
    )
set_target_properties(openvr_imported PROPERTIES IMPORTED_IMPLIB 
    "${EXTERNAL_LIBS}/openvr/lib/win64/openvr_api.lib"
    )
set_target_properties(openvr_imported PROPERTIES IMPORTED_LOCATION 
    "${EXTERNAL_LIBS}/openvr/bin/win64/openvr_api.dll"
    )

# tracker data recording app
add_executable(ovr-tracker-app "src/ovr_tracker_app.cpp")
target_link_libraries(ovr-tracker-app PRIVATE
    # openvr_api64
    openvr_imported
    )
target_precompile_headers(ovr-tracker-app PRIVATE
    "src/pch.h"
    )
target_compile_options(ovr-tracker-app PUBLIC "/MP")
target_link_options(ovr-tracker-app PUBLIC "/debug:fastlink" "/incremental")

# Helper for printing information about OpenVR connected devices
add_executable(ovr-report-connected-devices "src/ovr_report_connected_devices.cpp")
target_link_libraries(ovr-report-connected-devices PRIVATE
    openvr_imported
    )
target_precompile_headers(ovr-report-connected-devices PRIVATE
    "src/pch.h"
    )
target_compile_options(ovr-report-connected-devices PUBLIC "/MP")
target_link_options(ovr-report-connected-devices PUBLIC "/debug:fastlink" "/incremental")