mkdir -p build/{Debug,RelWithDebInfo}
cmake -H. -Bbuild -G"Visual Studio 16 2019" -A x64
cmake --build build --config Debug
cmake --build build --config RelWithDebInfo
cp libs/openvr/bin/win64/openvr_api.dll build/Debug/
cp libs/openvr/bin/win64/openvr_api.dll build/RelWithDebInfo/
cp build/libs/SDL2-2.0.14/Debug/SDL2d.dll build/Debug/
cp build/libs/SDL2-2.0.14/RelWithDebInfo/SDL2.dll build/RelWithDebInfo/
