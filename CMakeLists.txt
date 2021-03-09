cmake_minimum_required(VERSION 3.5.0)
project(ovr-tracker-app)

set(CMAKE_CXX_STANDARD 17)

find_package(OpenGL REQUIRED COMPONENTS OpenGL)

set(EXTERNAL_LIBS "${CMAKE_SOURCE_DIR}/libs")

# dependency: SDL2
set(SDL2_INCLUDE_DIR "${EXTERNAL_LIBS}/SDL2-2.0.14/include")
set(SDL2_LIBRARY "${EXTERNAL_LIBS}/SDL2-2.0.14/lib/x64/SDL2.lib")
set(SDL2MAIN_LIBRARY "${EXTERNAL_LIBS}/SDL2-2.0.14/lib/x64/SDL2main.lib")
add_library(sdl2_imported STATIC IMPORTED)
target_include_directories(sdl2_imported INTERFACE ${SDL2_INCLUDE_DIR})
set_target_properties(sdl2_imported PROPERTIES IMPORTED_LOCATION ${SDL2_LIBRARY})
add_library(sdl2main_imported STATIC IMPORTED)
set_target_properties(sdl2main_imported PROPERTIES IMPORTED_LOCATION ${SDL2MAIN_LIBRARY})

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
    sdl2_imported
    sdl2main_imported
    glew_imported
    opengl32.lib
    # openvr_api64
    openvr_imported
    )