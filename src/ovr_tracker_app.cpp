#include <iostream>
#include <vector>
#include <chrono>

#include "openvr.h"

// Quick app that reads vr tracker data through OpenVR and outputs timestamp and position as lines of json to stdout
int main(int argc, char *argv[])
{
    auto vr_error = vr::VRInitError_None;
    auto vr_system = vr::VR_Init( &vr_error, vr::VRApplication_Other );
    //auto vr_system = vr::VR_Init( &vr_error, vr::VRApplication_Background );

    if (vr_error != vr::VRInitError_None)
    {
	std::printf("Unable to init VR runtime: %s\n", vr::VR_GetVRInitErrorAsEnglishDescription(vr_error));
	return 1;
    }

    auto trackers = std::vector<size_t>();
    for (size_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i)
    {
        auto device_class = vr::VRSystem()->GetTrackedDeviceClass((vr::TrackedDeviceIndex_t)i);
        if (device_class == vr::TrackedDeviceClass_GenericTracker)
        {
            trackers.push_back(i);
        }
    }

    using clock = std::chrono::high_resolution_clock;
    auto all_poses = std::vector<vr::TrackedDevicePose_t>(vr::k_unMaxTrackedDeviceCount);
    auto t_start = clock::now();
    while (true) // TODO proper end condition, but ctrl+c works well of course
    {
        auto t_now = clock::now();
        vr::VRSystem()->GetDeviceToAbsoluteTrackingPose(
            vr::TrackingUniverseSeated, 0.0f, all_poses.data(), (uint32_t)all_poses.size());

	// ticks are in nanoseconds, so t is seconds
        auto t = (t_now - t_start).count() / 1'000'000'000.0;
        for (size_t i = 0; i < trackers.size(); ++i)
        {
            auto& m = all_poses[trackers[i]].mDeviceToAbsoluteTracking.m;
            std::printf(R"({ "time": %f, "tracker": %d, "position": { "x": %f, "y": %f, "z": %f } })",
                t, (int)i, m[0][3], m[1][3], m[2][3]);
            std::printf("\n");
        }
    }

    vr::VR_Shutdown();

    return 0;
}
