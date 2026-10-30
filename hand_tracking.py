"""MediaPipe Tasks hand tracking for the synchronous webcam loop."""

from pathlib import Path
import time

import cv2
import mediapipe as mp


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "assets" / "hand_landmarker.task"
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)


class HandTracker:
    def __init__(self, model_path=DEFAULT_MODEL_PATH, detection_confidence=0.7,
                 tracking_confidence=0.5):
        model_path = Path(model_path).expanduser().resolve()
        if not model_path.is_file():
            raise FileNotFoundError(
                f"Hand model not found: {model_path}. "
                "Run python scripts/download_model.py or pass --model PATH."
            )
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=detection_confidence,
            min_hand_presence_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self._detector = mp.tasks.vision.HandLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def process(self, rgb_frame):
        # Tasks requires increasing timestamps, even for frames in the same ms.
        timestamp_ms = max(time.monotonic_ns() // 1_000_000,
                           self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        return self._detector.detect_for_video(image, timestamp_ms)

    def close(self):
        self._detector.close()


def draw_hand_landmarks(frame, landmarks, connection_color, landmark_color):
    """Draw Tasks landmarks without depending on the removed Solutions API."""
    height, width = frame.shape[:2]
    points = [(int(point.x * width), int(point.y * height)) for point in landmarks]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], connection_color, 1)
    for point in points:
        cv2.circle(frame, point, 3, landmark_color, 1)
