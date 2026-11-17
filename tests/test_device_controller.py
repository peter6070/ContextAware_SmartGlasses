"""시리얼 명령, 응답 및 실패를 검증합니다."""
import unittest
from software.device_controller import DeviceController


class FakeSerial:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def readline(self):
        return next(self.responses)


class DeviceControllerTests(unittest.TestCase):
    def test_selection_action_and_clear(self):
        link = FakeSerial([b"OK\r\n"] * 3)
        controller = DeviceController(link)
        controller.select("FAN")
        controller.send("FAN,START")
        controller.select(None)
        self.assertEqual(link.writes, [b"SELECT,FAN\n", b"FAN,START\n", b"SELECT,NONE\n"])

    def test_failed_command_and_timeout(self):
        link = FakeSerial([b"ERR,FAN_NOT_CONFIGURED\n", b""])
        controller = DeviceController(link)
        with self.assertRaisesRegex(RuntimeError, "FAN_NOT_CONFIGURED"):
            controller.send("FAN,START")
        with self.assertRaises(TimeoutError):
            controller.select(None)

    def test_unknown_selection_is_blocked(self):
        link = FakeSerial([])
        with self.assertRaises(ValueError):
            DeviceController(link).select("OTHER")
        self.assertEqual(link.writes, [])


if __name__ == "__main__":
    unittest.main()
