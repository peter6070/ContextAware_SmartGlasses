"""노트북의 Matter 자식 프로세스와 통신합니다."""
import json
import subprocess
import threading
import queue
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class MatterController:
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.process = subprocess.Popen(
            ['node', str(ROOT / 'matter_adapter' / 'controller.mjs')],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding='utf-8', bufsize=1,
        )
        self.lines = queue.Queue()
        self.lock = threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()
        try:
            if not self._receive().get('ready'):
                raise RuntimeError('Matter 컨트롤러를 시작하지 못했습니다.')
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                self.lines.put(line)
        finally:
            self.lines.put(None)

    def _receive(self, timeout=None):
        try:
            line = self.lines.get(timeout=timeout or self.timeout)
        except queue.Empty as exc:
            self.close()
            raise TimeoutError('Matter 응답 시간이 초과되었습니다.') from exc
        if line is None:
            raise RuntimeError('Matter 컨트롤러가 종료되었습니다.')
        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError('Matter 컨트롤러 응답을 해석할 수 없습니다.') from exc

    def request(self, op, timeout=None, **values):
        with self.lock:
            self.process.stdin.write(json.dumps({'op': op, **values}, ensure_ascii=True) + '\n')
            self.process.stdin.flush()
            response = self._receive(timeout)
            if not response.get('ok'):
                raise RuntimeError(response.get('error', 'Matter 요청에 실패했습니다.'))
            return response['result']

    def close(self):
        if self.process.poll() is None:
            if self.process.stdin:
                self.process.stdin.close()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()
