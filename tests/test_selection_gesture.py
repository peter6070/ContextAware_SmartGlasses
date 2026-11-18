"""하드웨어 없이 선택과 명령 전환을 검증합니다."""
import unittest
import numpy as np
from software.device_selector import DeviceSelector
from software.gesture_state_machine import GestureStateMachine
from software.command_router import route


def marker(x, y):
    return np.array([[x, y], [x+2, y], [x+2, y+2], [x, y+2]])


class SelectionGestureTests(unittest.TestCase):
    def test_selection_and_loss(self):
        selector = DeviceSelector({1: "LIGHT", 2: "CURTAIN"}, 1, 2)
        detections = [(1, marker(0, 0)), (2, marker(49, 49))]
        self.assertIsNone(selector.update(detections, (100, 100), 0))
        self.assertEqual(selector.update(detections, (100, 100), 1), "CURTAIN")
        self.assertEqual(selector.update([], (100, 100), 2), "CURTAIN")
        self.assertIsNone(selector.update([], (100, 100), 3.1))

    def test_transition_and_loss(self):
        state = GestureStateMachine(0.5, 1)
        self.assertIsNone(state.update("FIST", 0))
        self.assertIsNone(state.update("FIST", 0.5))
        self.assertIsNone(state.update("PALM", 0.6))
        self.assertEqual(state.update("PALM", 1.1), "ACTIVATE")
        self.assertIsNone(state.update("PALM", 2))
        self.assertIsNone(state.update(None, 3))
        self.assertIsNone(state.update("FIST", 3.5))
        self.assertIsNone(state.update("FIST", 4.1))

    def test_brief_unclassified_pose_preserves_transition(self):
        state = GestureStateMachine()
        state.update("FIST", 0)
        state.update("FIST", 0.5)
        self.assertIsNone(state.update(None, 0.6))
        self.assertIsNone(state.update("PALM", 0.8))
        self.assertEqual(state.update("PALM", 1.4), "ACTIVATE")
        self.assertIsNone(state.update("PALM", 2.5))

    def test_default_stabilizes_after_0_2_seconds(self):
        state = GestureStateMachine()
        self.assertIsNone(state.update("FIST", 0))
        self.assertIsNone(state.update("FIST", 0.21))
        self.assertIsNone(state.update("PALM", 0.3))
        self.assertIsNone(state.update("PALM", 0.49))
        self.assertEqual(state.update("PALM", 0.51), "ACTIVATE")

    def test_router_blocks_unselected(self):
        self.assertIsNone(route(None, "ACTIVATE"))
        self.assertEqual(route("LIGHT", "ACTIVATE"), "LIGHT,ON")
        self.assertEqual(route("CURTAIN", "DEACTIVATE"), "CURTAIN,CLOSE")

    def test_toggle_routes_both_directions(self):
        for device, on, off in (
            ("LIGHT", "LIGHT,ON", "LIGHT,OFF"),
            ("CURTAIN", "CURTAIN,OPEN", "CURTAIN,CLOSE"),
            ("FAN", "FAN,START", "FAN,STOP"),
        ):
            with self.subTest(device=device):
                self.assertEqual(route(device, "TOGGLE", active=False), on)
                self.assertEqual(route(device, "TOGGLE", active=True), off)


if __name__ == "__main__":
    unittest.main()
