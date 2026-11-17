"""MediaPipe Hand Landmarker 기반 주먹·손바닥 분류."""
import math
import cv2
import mediapipe as mp


class GestureRecognizer:
    def __init__(self, model_path):
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            num_hands=1)
        self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def recognize(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        if not result.hand_landmarks:
            return None
        hand = result.hand_landmarks[0]

        def distance(a, b):
            return math.hypot(hand[a].x - hand[b].x, hand[a].y - hand[b].y)

        scale = distance(0, 9)
        if scale < 0.01:
            return None
        extended = [distance(0, tip) > distance(0, pip) * 1.15
                    for tip, pip in [(8, 6), (12, 10), (16, 14), (20, 18)]]
        if all(extended):
            return "PALM"
        if not any(extended):
            return "FIST"
        return None

    def close(self):
        self.landmarker.close()
