import cv2
import time
import numpy as np
import HandTrackingModule as htm
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

w_cam, h_cam = 640, 480

cap = cv2.VideoCapture(0)
cap.set(3, w_cam)
cap.set(4, h_cam)
p_time = 0

# Using updated snake_case parameter names
detector = htm.HandDetector(detection_con=0.7, max_hands=1)

try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_,
        CLSCTX_ALL,
        None
    )
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    min_vol, max_vol, _ = volume.GetVolumeRange()
    print("SUCCESS: Audio Connected!")
except Exception as e:
    print("Audio Error:", e)
    exit()

vol_bar = 400
vol_per = 0
color_vol = (255, 0, 0)

while True:
    success, img = cap.read()
    if not success: break

    # Calling updated snake_case methods
    img = detector.find_hands(img)
    lm_list, bbox = detector.find_position(img, draw=True)

    if len(lm_list) != 0:
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100
        if 150 < area < 1000:
            length, img, line_info = detector.find_distance(4, 8, img)

            vol_bar = np.interp(length, [50, 200], [400, 150])
            vol_per = np.interp(length, [50, 200], [0, 100])

            smoothness = 5
            vol_per = smoothness * round(vol_per / smoothness)
            fingers = detector.fingers_up()

            # Set volume ONLY if pinky is down (Lock mechanism)
            if not fingers[4]:
                volume.SetMasterVolumeLevelScalar(vol_per / 100, None)
                cv2.circle(img, (line_info[4], line_info[5]), 15, (0, 255, 0), cv2.FILLED)
                color_vol = (0, 255, 0)
            else:
                color_vol = (255, 0, 0)

    # Drawing UI
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(vol_bar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(vol_per)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    c_vol = int(volume.GetMasterVolumeLevelScalar() * 100)
    cv2.putText(img, f'System Vol: {int(c_vol)}', (320, 50), cv2.FONT_HERSHEY_COMPLEX, 1, color_vol, 3)

    c_time = time.time()
    fps = 1 / (c_time - p_time)
    p_time = c_time
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

    cv2.imshow("Hand Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()