#include <cstdio>

#include "openvr.h"

void report_connected_devices(vr::IVRSystem* vr_system)
{
    char string_prop_value[vr::k_unMaxPropertyStringSize];

    for (size_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i)
    {
        auto device_class = vr_system->GetTrackedDeviceClass((vr::TrackedDeviceIndex_t)i);
        if (device_class != vr::TrackedDeviceClass_Invalid)
        {
            std::printf("Device %d:\n", (int)i);
            auto props_and_names = {
                std::make_pair(vr::Prop_TrackingSystemName_String, "vr::Prop_TrackingSystemName_String"),
                std::make_pair(vr::Prop_ModelNumber_String, "vr::Prop_ModelNumber_String")
            };
            for (auto [prop, name] : props_and_names)
            {
                auto error = vr::TrackedProp_Success;
                vr_system->GetStringTrackedDeviceProperty((vr::TrackedDeviceIndex_t)i, prop, string_prop_value, vr::k_unMaxPropertyStringSize, &error);
                if (error != vr::TrackedProp_Success)
                {
                    std::printf("    Failed to read device property '%s', error: %s\n", name, vr_system->GetPropErrorNameFromEnum(error));
                }
                else
                {
                    std::printf("    %s: %s\n", name, string_prop_value);
                }
            }
        }
    }
}

// Quick app that prints information about currently connected OpenVR devices
int main(int argc, char *argv[])
{
    auto vr_error = vr::VRInitError_None;
    auto vr_system = vr::VR_Init(&vr_error, vr::VRApplication_Other);
    if (vr_error != vr::VRInitError_None)
    {
        std::printf("Unable to init VR runtime: %s\n", vr::VR_GetVRInitErrorAsEnglishDescription(vr_error));
        return 1;
    }
    report_connected_devices(vr_system);
}