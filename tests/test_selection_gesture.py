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
        self.assertIsNone(state.update("FIST", 3.1))
        self.assertIsNone(state.update("FIST", 3.7))

    def test_router_blocks_unselected(self):
        self.assertIsNone(route(None, "ACTIVATE"))
        self.assertEqual(route("LIGHT", "ACTIVATE"), "LIGHT,ON")
        self.assertEqual(route("CURTAIN", "DEACTIVATE"), "CURTAIN,CLOSE")


if __name__ == "__main__":
    unittest.main()
