import contextlib
import io
import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

import app
from hand_tracking import HandTracker


class RecordingKeyboard:
    def __init__(self):
        self.held = set()
        self.events = []

    def press(self, key):
        self.held.add(key)
        self.events.append(("press", key))

    def release(self, key):
        self.held.discard(key)
        self.events.append(("release", key))


def hand(x, y, opened=False):
    landmarks = [SimpleNamespace(x=x, y=y, z=0) for _ in range(21)]
    for tip in (8, 12, 16, 20):
        landmarks[tip] = SimpleNamespace(x=x, y=y - 0.1 if opened else y + 0.1, z=0)
    return landmarks


class SteeringTests(unittest.TestCase):
    def setUp(self):
        self.keyboard = RecordingKeyboard()
        self.controller = app.VirtualSteeringController(self.keyboard)

    def steer(self, degrees):
        return self.controller.update_steer((0, 0), (100, 100 * math.tan(math.radians(degrees))))

    def test_deadzone_and_hysteresis_in_both_directions(self):
        for sign, key, direction in ((-1, app.Key.left, "LEFT"), (1, app.Key.right, "RIGHT")):
            with self.subTest(direction=direction):
                self.controller.release_all()
                self.assertEqual(self.steer(sign * 10)[1], "STRAIGHT")
                self.assertEqual(self.steer(sign * 20)[1], direction)
                self.assertEqual(self.steer(sign * 9)[1], direction)
                self.assertIn(key, self.keyboard.held)
                self.assertGreaterEqual(self.steer(sign * 9)[2], 0)
                self.assertEqual(self.steer(sign * 5)[1], "STRAIGHT")
                self.assertNotIn(key, self.keyboard.held)

    def test_reversed_hand_order_does_not_turn_straight_into_180_degrees(self):
        angle, direction, _ = self.controller.update_steer((500, 200), (100, 200))
        self.assertEqual(angle, 0)
        self.assertEqual(direction, "STRAIGHT")

    def test_direction_reversal_releases_opposite_key_first(self):
        self.steer(-20)
        self.steer(20)
        self.assertEqual(self.keyboard.events[-2:], [("release", app.Key.left), ("press", app.Key.right)])
        self.assertEqual(self.keyboard.held, {app.Key.right})

    def test_throttle_transitions_and_no_duplicate_presses(self):
        self.assertEqual(self.controller.update_throttle(False, False), "ACCEL")
        self.controller.update_throttle(False, False)
        self.assertEqual(self.keyboard.events, [("press", app.Key.up)])
        self.assertEqual(self.controller.update_throttle(True, True), "BRAKE")
        self.assertEqual(self.keyboard.held, {app.Key.down})
        self.assertEqual(self.controller.update_throttle(True, False), "NEUTRAL")
        self.assertFalse(self.keyboard.held)

    def test_release_all_only_releases_keys_this_app_holds(self):
        self.controller.update_throttle(False, False)
        self.controller.release_all()
        self.controller.release_all()
        self.assertEqual(self.keyboard.events, [("press", app.Key.up), ("release", app.Key.up)])

    def test_failed_release_is_retried_on_cleanup(self):
        keyboard = Mock()
        controller = app.VirtualSteeringController(keyboard)
        controller.update_throttle(False, False)
        keyboard.release.side_effect = [RuntimeError("temporary error"), None]
        with contextlib.redirect_stdout(io.StringIO()):
            controller.release_all()
        self.assertTrue(controller.keys_held[app.Key.up])
        controller.release_all()
        self.assertFalse(controller.keys_held[app.Key.up])

    def test_tasks_landmark_gestures(self):
        self.assertFalse(app.is_hand_open(hand(0.3, 0.5)))
        self.assertTrue(app.is_hand_open(hand(0.3, 0.5, opened=True)))


class CameraTests(unittest.TestCase):
    @patch("app.platform.system", return_value="Windows")
    @patch("app.cv2.VideoCapture")
    def test_windows_falls_back_and_releases_failed_backend(self, factory, _):
        failed, working = Mock(), Mock()
        failed.isOpened.return_value = False
        working.isOpened.return_value = True
        factory.side_effect = [failed, working]
        self.assertIs(app.open_camera(2), working)
        failed.release.assert_called_once()
        self.assertEqual([call.args for call in factory.call_args_list], [(2, app.cv2.CAP_DSHOW), (2, app.cv2.CAP_ANY)])

    @patch("app.platform.system", return_value="Linux")
    @patch("app.cv2.VideoCapture")
    def test_non_windows_uses_portable_backend(self, factory, _):
        factory.return_value.isOpened.return_value = True
        app.open_camera(1)
        factory.assert_called_once_with(1, app.cv2.CAP_ANY)

    @patch("app.platform.system", return_value="Windows")
    @patch("app.cv2.VideoCapture")
    def test_all_backends_fail_with_actionable_error(self, factory, _):
        factory.return_value.isOpened.return_value = False
        with self.assertRaisesRegex(RuntimeError, "--camera INDEX"):
            app.open_camera(3)
        self.assertEqual(factory.return_value.release.call_count, 2)


class TrackingTests(unittest.TestCase):
    def test_missing_model_explains_recovery(self):
        with self.assertRaisesRegex(FileNotFoundError, "download_model.py"):
            HandTracker("assets/does-not-exist.task")

    @patch("hand_tracking.time.monotonic_ns", return_value=2_000_000)
    def test_multiple_frames_within_one_millisecond_get_unique_timestamps(self, _):
        tracker = HandTracker.__new__(HandTracker)
        tracker._detector = Mock()
        tracker._last_timestamp_ms = -1
        for _ in range(3):
            tracker.process(np.zeros((48, 64, 3), dtype=np.uint8))
        self.assertEqual([call.args[1] for call in tracker._detector.detect_for_video.call_args_list], [2, 3, 4])


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.camera = Mock()
        self.camera.read.side_effect = lambda: (True, np.zeros((480, 640, 3), dtype=np.uint8))
        self.detector = Mock()
        self.keyboard = RecordingKeyboard()
        self.controller = app.VirtualSteeringController(self.keyboard)
        self.gui = contextlib.ExitStack()
        self.addCleanup(self.gui.close)
        self.gui.enter_context(patch("app.cv2.imshow"))
        self.gui.enter_context(patch("app.cv2.getWindowProperty", return_value=1))
        self.wait_key = self.gui.enter_context(patch("app.cv2.waitKey", return_value=ord("q")))
        self.gui.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def run_loop(self):
        app.run_loop(self.camera, self.detector, self.controller)

    def test_tasks_results_use_pixel_angles_and_screen_order(self):
        self.detector.process.return_value = SimpleNamespace(hand_landmarks=[hand(0.7, 0.6), hand(0.3, 0.4)])
        angles = []
        self.wait_key.side_effect = lambda _: angles.append(self.controller.steering_angle_history[-1]) or ord("q")
        self.run_loop()
        self.assertAlmostEqual(angles[0], math.degrees(math.atan2(96, 256)))
        self.assertIn(("press", app.Key.up), self.keyboard.events)
        self.assertFalse(self.keyboard.held)

    def test_tracking_loss_releases_after_grace_period(self):
        self.detector.process.side_effect = [SimpleNamespace(hand_landmarks=[hand(0.3, 0.5), hand(0.7, 0.5)])] + [SimpleNamespace(hand_landmarks=[])] * app.HAND_TRACKING_GRACE_FRAMES
        snapshots = []
        def next_key(_):
            snapshots.append(set(self.keyboard.held))
            return ord("q") if len(snapshots) == app.HAND_TRACKING_GRACE_FRAMES + 1 else -1
        self.wait_key.side_effect = next_key
        self.run_loop()
        self.assertIn(app.Key.up, snapshots[-2])
        self.assertFalse(snapshots[-1])

    def test_failed_camera_read_releases_held_keys_and_stops(self):
        self.controller.update_throttle(False, False)
        self.camera.read.side_effect = [(False, None)]
        with self.assertRaisesRegex(RuntimeError, "Camera stopped"):
            self.run_loop()
        self.assertFalse(self.keyboard.held)
        self.detector.process.assert_not_called()

    def test_inference_error_releases_held_keys(self):
        self.controller.update_throttle(False, False)
        self.detector.process.side_effect = RuntimeError("inference failed")
        with self.assertRaisesRegex(RuntimeError, "inference failed"):
            self.run_loop()
        self.assertFalse(self.keyboard.held)

    @patch("app.cv2.getWindowProperty", return_value=0)
    def test_closed_window_exits(self, _):
        self.detector.process.return_value = SimpleNamespace(hand_landmarks=[])
        self.wait_key.return_value = -1
        self.run_loop()
        self.camera.read.assert_called_once()


class StartupTests(unittest.TestCase):
    @patch("app.cv2.destroyAllWindows")
    @patch("app.open_camera", side_effect=RuntimeError("no camera"))
    @patch("app.HandTracker")
    def test_camera_startup_failure_closes_detector(self, tracker, _, destroy):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main(["--preview"]), 1)
        tracker.return_value.close.assert_called_once()
        destroy.assert_called_once()

    @patch("app.cv2.destroyAllWindows")
    @patch("app.run_loop", side_effect=RuntimeError("loop error"))
    @patch("app.Controller")
    @patch("app.open_camera")
    @patch("app.HandTracker")
    def test_preview_does_not_construct_real_keyboard_and_cleans_up(self, tracker, camera, keyboard, loop, destroy):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.main(["--preview"]), 1)
        keyboard.assert_not_called()
        tracker.return_value.close.assert_called_once()
        camera.return_value.release.assert_called_once()
        destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
