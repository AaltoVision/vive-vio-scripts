#include <iostream>
#include <vector>
#include <chrono>

#include "openvr.h"

// TODO: possibly log real world time, not starting from t=0

// Quick app that reads vr tracker data through OpenVR and outputs timestamp and position as lines of json to stdout
int main(int argc, char *argv[])
{
    auto vr_error = vr::VRInitError_None;
    auto vr_system = vr::VR_Init(&vr_error, vr::VRApplication_Other);
    if (vr_error != vr::VRInitError_None)
    {
        std::printf("Unable to init VR runtime: %s\n", vr::VR_GetVRInitErrorAsEnglishDescription(vr_error));
        return 1;
    }

    auto trackers = std::vector<size_t>();
    for (size_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i)
    {
        auto device_class = vr_system->GetTrackedDeviceClass((vr::TrackedDeviceIndex_t)i);
        if (device_class == vr::TrackedDeviceClass_GenericTracker)
        {
            trackers.push_back(i);
        }
    }

    using clock = std::chrono::high_resolution_clock;
    auto all_poses = std::vector<vr::TrackedDevicePose_t>(vr::k_unMaxTrackedDeviceCount);
    auto t_start = clock::now();
    auto t_previous = clock::now();

    // TODO proper end condition, ctrl+c mostly works, but printf may not finish flush fully,
    // leaving an incomplete line at the end of data
    while (true)
    {
        auto t_now = clock::now();

        // if ((t_now - t_previous).count() < (1./60.)*1'000'000'000) continue; // sample at ~60Hz

        vr_system->GetDeviceToAbsoluteTrackingPose(
            vr::TrackingUniverseSeated, 0.0f, all_poses.data(), (uint32_t)all_poses.size());

        // ticks are in nanoseconds, so t is seconds
        auto t = (t_now - t_start).count() / 1'000'000'000.0;
        for (size_t i = 0; i < trackers.size(); ++i)
        {
            auto& m = all_poses[trackers[i]].mDeviceToAbsoluteTracking.m;
            // std::printf(R"({ "time": %f, "tracker": %d, "position": { "x": %f, "y": %f, "z": %f }, "rotation": { "x": %f, "y": %f, "z": %f, "w": %f } })",
            //     t, (int)i, m[0][3], m[1][3], m[2][3], 0.0f, 0.0f, 0.0f, 0.0f);

            std::printf(R"({ "time": %f, "tracker": %d, "position": { "x": %f, "y": %f, "z": %f }, "rotation": { "col0": [ %f, %f, %f ], "col1": [ %f, %f, %f ], "col2": [ %f, %f, %f ] } })",
                t, (int)i, m[0][3], m[1][3], m[2][3],
                m[0][0], m[0][1], m[0][2],
                m[1][0], m[1][1], m[1][2],
                m[2][0], m[2][1], m[2][2]
                );

            std::printf("\n");
        }
        auto t_previous = t_now;
    }

    vr::VR_Shutdown();

    return 0;
}
