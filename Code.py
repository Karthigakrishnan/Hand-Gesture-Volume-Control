import cv2
import mediapipe as mp
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import keyboard

# Webcam and hand tracking setup
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Volume control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
min_vol, max_vol = volume_ctrl.GetVolumeRange()[:2]

# Previous distance to avoid jitter
prev_length = 0
threshold = 5  # Minimum change needed to update volume

while True:
    success, img = cap.read()
    if not success:
        break  # Exit if the webcam is not accessible

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    lm_list = []
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                lm_list.append((id, int(lm.x * w), int(lm.y * h)))

            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)

        if lm_list:
            x1, y1 = lm_list[4][1], lm_list[4][2]
            x2, y2 = lm_list[8][1], lm_list[8][2]
            length = math.hypot(x2 - x1, y2 - y1)

            # Only update volume if hand gesture changes significantly
            if abs(length - prev_length) > threshold:
                vol = np.interp(length, [20, 180], [min_vol, max_vol])
                volume_ctrl.SetMasterVolumeLevel(vol, None)
                prev_length = length

            # Drawing
            cv2.circle(img, (x1, y1), 10, (0,255,0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (0,255,0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (0,255,0), 3)

            # Volume length text
            cv2.putText(img, f'Gesture Length: {int(length)}', (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    # Show image
    cv2.imshow("Volume Control", img)

    # Exit on pressing 'q' or 'ESC'
    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or key == 27 or keyboard.is_pressed('q'):
        break

cap.release()
cv2.destroyAllWindows()
