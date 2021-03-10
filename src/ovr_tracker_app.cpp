#include <cstdio>
#include <iostream>
#include <vector>
#include <iterator>
#include <chrono>

#include <SDL.h>
#include <GL/glew.h>
#include <SDL_opengl.h>

#include "openvr.h"

int main(int argc, char *argv[])
{
    if ( SDL_Init( SDL_INIT_VIDEO | SDL_INIT_TIMER ) < 0 )
    {
        printf("%s - SDL could not initialize! SDL Error: %s\n", __FUNCTION__, SDL_GetError());
        return false;
    }

    auto eError = vr::VRInitError_None;
    auto m_pHMD = vr::VR_Init( &eError, vr::VRApplication_Other );

	if ( eError != vr::VRInitError_None )
	{
		m_pHMD = NULL;
		char buf[1024];
		sprintf_s( buf, sizeof( buf ), "Unable to init VR runtime: %s", vr::VR_GetVRInitErrorAsEnglishDescription( eError ) );
		SDL_ShowSimpleMessageBox( SDL_MESSAGEBOX_ERROR, "VR_Init Failed", buf, NULL );
		return 1;
	}

    std::printf("Trackers:\n");
    auto trackers = std::vector<size_t>();
    for (size_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i)
    {
        auto device_class = vr::VRSystem()->GetTrackedDeviceClass((vr::TrackedDeviceIndex_t)i);
        if (device_class == vr::TrackedDeviceClass_GenericTracker)
        {
            trackers.push_back(i);
            std::printf("\tind: %d, class: %d\n", (int)i, device_class);
        }
    }

    using clock = std::chrono::high_resolution_clock;
    auto t_start = clock::now();
    while (true)
    {
        auto t_now = clock::now();
        auto all_poses = std::vector<vr::TrackedDevicePose_t>(vr::k_unMaxTrackedDeviceCount);
        vr::VRSystem()->GetDeviceToAbsoluteTrackingPose(
            vr::TrackingUniverseSeated, 0.0f, all_poses.data(), (uint32_t)all_poses.size());

        auto debug_print_pose = [](vr::TrackedDevicePose_t const& pose)
        {
            std::printf("Tracking result: %d\n", (int)pose.eTrackingResult);
            std::printf("Connected: %d\n", (int)pose.bDeviceIsConnected);
            std::printf("Valid: %d\n", pose.bPoseIsValid ? 1 : 0);
            auto& m = pose.mDeviceToAbsoluteTracking.m;
            std::printf("Pose:\n\t%.2f %.2f %.2f %.2f\n\t%.2f %.2f %.2f %.2f\n\t%.2f %.2f %.2f %.2f\n",
                        m[0][0], m[0][1], m[0][2], m[0][3],
                        m[1][0], m[1][1], m[1][2], m[1][3],
                        m[2][0], m[2][1], m[2][2], m[2][3]);
        };
        auto print_position = [](vr::TrackedDevicePose_t const& pose)
        {
            auto& m = pose.mDeviceToAbsoluteTracking.m;
            std::printf("Position:\t%.2f %.2f %.2f\n", m[0][3], m[1][3], m[2][3]);
        };

        auto t = (t_now - t_start).count() / 1'000'000'000.0;
        for (size_t i = 0; i < trackers.size(); ++i)
        {
            // debug_print_pose(all_poses[trackers[i]]);
            // print_position(all_poses[trackers[i]]);

            auto& m = all_poses[trackers[i]].mDeviceToAbsoluteTracking.m;
            std::printf(R"({ "time": %f, "position": { "x": %f, "y": %f, "z": %f } })",
                t, m[0][3], m[1][3], m[2][3]);
            std::printf("\n");
        }
    }

    vr::VR_Shutdown();

    return 0;
}
