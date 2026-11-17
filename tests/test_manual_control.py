"""실제 부품 없이 수동 제어의 시리얼 동작을 검증합니다."""
import queue
import time
import unittest
from software.manual_control import ArduinoService


class FakeSerial:
    def __init__(self, *args, **kwargs):
        self.writes = []
        self.replies = queue.Queue()
        self.closed = False

    def reset_input_buffer(self):
        pass

    def write(self, data):
        self.writes.append(data)
        self.replies.put(b'OK\n')

    def readline(self):
        return self.replies.get(timeout=1)

    def close(self):
        self.closed = True


class ManualControlTests(unittest.TestCase):
    def test_select_before_command_and_close(self):
        events = queue.Queue()
        serial = FakeSerial()
        service = ArduinoService(lambda *event: events.put(event), lambda *a, **k: serial, lambda _: None)
        service.submit('connect', 'COM_TEST')
        self.assertIn('연결 중', events.get(timeout=2)[1])
        self.assertEqual(events.get(timeout=2), ('arduino', 'COM_TEST 연결됨'))
        service.submit('command', 'FAN', 'FAN,START')
        self.assertIn('FAN,START', events.get(timeout=2)[1])
        service.submit('stop')
        service.worker.join(timeout=2)
        self.assertFalse(service.worker.is_alive())
        self.assertEqual(serial.writes, [b'SELECT,NONE\n', b'SELECT,FAN\n', b'FAN,START\n', b'SELECT,NONE\n'])
        self.assertTrue(serial.closed)

    def test_command_without_connection_is_rejected(self):
        events = queue.Queue()
        service = ArduinoService(lambda *event: events.put(event))
        service.submit('command', 'LIGHT', 'LIGHT,ON')
        self.assertIn('먼저 Arduino', events.get(timeout=2)[1])
        service.submit('stop')
        service.worker.join(timeout=2)

    def test_connection_without_response_reports_failure_and_closes(self):
        events = queue.Queue()
        serial = FakeSerial()
        serial.readline = lambda: b''
        service = ArduinoService(lambda *event: events.put(event), lambda *a, **k: serial, lambda _: None)
        service.submit('connect', 'COM_TEST')
        received = [events.get(timeout=2) for _ in range(4)]
        self.assertTrue(any(kind == 'arduino' and '연결 실패' in value for kind, value in received))
        self.assertTrue(any('응답하지 않습니다' in value for _, value in received))
        self.assertTrue(serial.closed)
        service.submit('stop')
        service.worker.join(timeout=2)


if __name__ == '__main__':
    unittest.main()
