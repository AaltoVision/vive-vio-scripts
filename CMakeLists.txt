cmake_minimum_required(VERSION 3.5.0)
project(ovr-tracker-app)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenGL REQUIRED COMPONENTS OpenGL)

set(EXTERNAL_LIBS "${CMAKE_SOURCE_DIR}/libs")

# # dependency: SDL2
add_subdirectory("${EXTERNAL_LIBS}/SDL2-2.0.14")

# dependency: glew
add_library(glew_imported STATIC IMPORTED)
target_include_directories(glew_imported INTERFACE
    "${EXTERNAL_LIBS}/glew-2.2.0/include/"
    )
set_target_properties(glew_imported PROPERTIES IMPORTED_LOCATION 
    "${EXTERNAL_LIBS}/glew-2.2.0/lib/Release/x64/glew32.lib"
    )

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

# app
add_executable(ovr-tracker-app "src/ovr_tracker_app.cpp")
target_link_libraries(ovr-tracker-app PRIVATE
    SDL2
    SDL2main
    glew_imported
    opengl32.lib
    # openvr_api64
    openvr_imported
    )