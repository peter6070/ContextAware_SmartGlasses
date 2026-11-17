"""로컬 Matter 프로세스의 오류 응답을 확인합니다."""
import unittest
from unittest.mock import MagicMock, patch
from software.matter_controller import MatterController


class MatterControllerTests(unittest.TestCase):
    def test_error_is_propagated(self):
        controller = MatterController.__new__(MatterController)
        controller.lock = __import__('threading').Lock()
        controller.process = MagicMock()
        with patch.object(controller, '_receive', return_value={'ok': False, 'error': '연결 실패'}):
            with self.assertRaisesRegex(RuntimeError, '연결 실패'):
                controller.request('on', id='peer1')
        controller.process.stdin.write.assert_called_once_with('{"op": "on", "id": "peer1"}\n')

    def test_timeout_closes_process(self):
        import queue
        controller = MatterController.__new__(MatterController)
        controller.timeout = 0.001
        controller.lines = queue.Queue()
        with patch.object(controller, 'close') as close:
            with self.assertRaises(TimeoutError):
                controller._receive()
            close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
