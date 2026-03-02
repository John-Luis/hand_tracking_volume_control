import cv2
import time
import numpy as np
import HandTrackingModule as htm
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

################################
wCam, hCam = 640, 480
################################

cap = cv2.VideoCapture(0)  # Changed to 0 for default webcam
cap.set(3, wCam)
cap.set(4, hCam)
pTime = 0

detector = htm.handDetector(detectionCon=0.7, maxHands=1)

# --- ROBUST AUDIO INITIALIZATION ---
try:
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol = volRange[0]
    maxVol = volRange[1]
except Exception as e:
    print(f"Audio Error: {e}. Try plugging in headphones or checking default playback device.")
    exit()

vol = 0
volBar = 400
volPer = 0
area = 0
colorVol = (255, 0, 0)

while True:
    success, img = cap.read()
    if not success: break

    # Find Hand
    img = detector.findHands(img)
    # Ensure findPosition returns the list and the bbox correctly
    lmList, bbox = detector.findPosition(img, draw=True)

    if len(lmList) != 0:
        # Filter based on size (Area of bounding box)
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) // 100

        if 150 < area < 1000:  # Adjusted range slightly for better sensitivity
            # Find Distance between index (8) and Thumb (4)
            length, img, lineInfo = detector.findDistance(4, 8, img)

            # Convert Volume (Interpolation)
            # Adjust [50, 200] if your hand is closer/further from camera
            volBar = np.interp(length, [50, 200], [400, 150])
            volPer = np.interp(length, [50, 200], [0, 100])

            # Reduce Resolution to make it smoother
            smoothness = 5
            volPer = smoothness * round(volPer / smoothness)

            # Check fingers up
            fingers = detector.fingersUp()

            # If pinky is down, set volume (Locked mode)
            if not fingers[4]:
                volume.SetMasterVolumeLevelScalar(volPer / 100, None)
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                colorVol = (0, 255, 0)
            else:
                colorVol = (255, 0, 0)

    # Drawing the Volume Bar
    cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
    cv2.putText(img, f'{int(volPer)} %', (40, 450), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)

    # Show current system volume level
    cVol = int(volume.GetMasterVolumeLevelScalar() * 100)
    cv2.putText(img, f'Vol Set: {int(cVol)}', (350, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, colorVol, 3)

    # Frame rate calculation
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (40, 50), cv2.FONT_HERSHEY_COMPLEX,
                1, (255, 0, 0), 3)

    cv2.imshow("Hand Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()