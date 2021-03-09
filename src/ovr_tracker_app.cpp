#include <cstdio>
#include <iostream>
#include <vector>
#include <iterator>

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
    auto m_pHMD = vr::VR_Init( &eError, vr::VRApplication_Background );

	if ( eError != vr::VRInitError_None )
	{
		m_pHMD = NULL;
		char buf[1024];
		sprintf_s( buf, sizeof( buf ), "Unable to init VR runtime: %s", vr::VR_GetVRInitErrorAsEnglishDescription( eError ) );
		SDL_ShowSimpleMessageBox( SDL_MESSAGEBOX_ERROR, "VR_Init Failed", buf, NULL );
		return 1;
	}

    auto trackers = std::vector<size_t>();
    for (size_t i = 0; i < vr::k_unMaxTrackedDeviceCount; ++i)
    {
        auto device_class = vr::VRSystem()->GetTrackedDeviceClass((vr::TrackedDeviceIndex_t)i);
        if (device_class == vr::TrackedDeviceClass_GenericTracker)
        {
            trackers.push_back(i);
            std::printf("ind: %d, class: %d\n", (int)i, device_class);
        }
    }

	// virtual void GetDeviceToAbsoluteTrackingPose( ETrackingUniverseOrigin eOrigin, float fPredictedSecondsToPhotonsFromNow, VR_ARRAY_COUNT(unTrackedDevicePoseArrayCount) TrackedDevicePose_t *pTrackedDevicePoseArray, uint32_t unTrackedDevicePoseArrayCount ) = 0;
    auto tracker_pose = vr::TrackedDevicePose_t{};
    vr::VRSystem()->GetDeviceToAbsoluteTrackingPose(vr::TrackingUniverseSeated, 0.0f, &tracker_pose, 1);

    std::printf("Tracking result: %d\n", (int)tracker_pose.eTrackingResult);
    std::printf("Connected: %d\n", (int)tracker_pose.bDeviceIsConnected);
    std::printf("Valid: %d\n", tracker_pose.bPoseIsValid ? 1 : 0);
    auto& m = tracker_pose.mDeviceToAbsoluteTracking.m;
    std::printf("Pose:\n\t%.2f %.2f %.2f %.2f\n\t%.2f %.2f %.2f %.2f\n\t%.2f %.2f %.2f %.2f\n",
                m[0][0], m[0][1], m[0][2], m[0][3],
                m[1][0], m[1][1], m[1][2], m[1][3],
                m[2][0], m[2][1], m[2][2], m[2][3]);

    // auto tracker_count = vr::VRSystem()->GetSortedTrackedDeviceIndicesOfClass(
    //     vr::TrackedDeviceClass_GenericTracker, nullptr, 0);
    // auto trackers = std::vector<vr::TrackedDeviceIndex_t>(tracker_count);
    // vr::VRSystem()->GetSortedTrackedDeviceIndicesOfClass(
    //     vr::TrackedDeviceClass_GenericTracker, trackers.data(), tracker_count);
    // std::cout << tracker_count << std::endl;
    // std::copy(trackers.begin(), trackers.end(), std::ostream_iterator<vr::TrackedDeviceIndex_t>(std::cout, ", "));

    vr::VR_Shutdown();

    return 0;
}
