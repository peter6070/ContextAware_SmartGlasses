"""Matter 명령을 영상 루프와 분리해 실행합니다."""
import queue
import threading
from software.matter_controller import MatterController


class MatterWorker:
    def __init__(self, device_id):
        self.device_id = device_id
        self.controller = MatterController()
        self.queue = queue.Queue(maxsize=1)
        self.results = queue.Queue()
        self.lock = threading.Lock()
        self.busy = False
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def submit(self, action):
        if action not in ('ACTIVATE', 'DEACTIVATE'):
            return False
        with self.lock:
            if self.busy:
                return False
            self.busy = True
            self.queue.put_nowait('on' if action == 'ACTIVATE' else 'off')
            return True

    def _run(self):
        while True:
            op = self.queue.get()
            if op is None:
                break
            try:
                result = self.controller.request(op, id=self.device_id)
                self.results.put(('ok', result))
            except (OSError, RuntimeError, TimeoutError) as error:
                self.results.put(('error', str(error)))
            finally:
                with self.lock:
                    self.busy = False

    def close(self):
        # 대기 중 명령은 실행하지 않고 폐기합니다.
        try:
            while True:
                self.queue.get_nowait()
        except queue.Empty:
            pass
        self.queue.put_nowait(None)
        self.thread.join(timeout=1)
        self.controller.close()
