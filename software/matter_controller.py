"""노트북의 Matter 자식 프로세스와 통신합니다."""
import json
import atexit
import subprocess
import threading
import queue
import time
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
        self.close_lock = threading.Lock()
        atexit.register(self.close)
        threading.Thread(target=self._read, daemon=True).start()
        try:
            response = self._receive()
            if not response.get('ready'):
                raise RuntimeError(response.get('error', 'Matter 컨트롤러를 시작하지 못했습니다.'))
        except BaseException:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                self.lines.put(line)
        finally:
            self.lines.put(None)

    def _receive(self, timeout=None, on_progress=None):
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        last_stage = None
        while True:
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise queue.Empty()
                line = self.lines.get(timeout=remaining)
            except queue.Empty as exc:
                self.close()
                stage = f' 마지막 단계는 {last_stage}입니다.' if last_stage else ''
                raise TimeoutError(f'Matter 응답 시간이 초과되었습니다.{stage}') from exc
            if line is None:
                raise RuntimeError('Matter 컨트롤러가 종료되었습니다.')
            try:
                response = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError('Matter 컨트롤러 응답을 해석할 수 없습니다.') from exc
            if 'progress' not in response:
                return response
            last_stage = response['progress']
            if on_progress is not None:
                on_progress(last_stage)

    def request(self, op, timeout=None, on_progress=None, **values):
        with self.lock:
            if self.closed:
                raise RuntimeError('Matter 컨트롤러가 종료되었습니다.')
            self.process.stdin.write(json.dumps({'op': op, **values}, ensure_ascii=True) + '\n')
            self.process.stdin.flush()
            response = self._receive(timeout, on_progress)
            if not response.get('ok'):
                raise RuntimeError(response.get('error', 'Matter 요청에 실패했습니다.'))
            return response['result']

    def commission(self, code, ssid, password, on_progress=None):
        return self.request('commission', timeout=300, on_progress=on_progress,
                            code=code, ssid=ssid, password=password)

    @property
    def closed(self):
        return self.process.poll() is not None or self.process.stdin.closed

    def close(self):
        with self.close_lock:
            atexit.unregister(self.close)
            if self.process.poll() is None:
                self.process.stdin.close()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            for stream in (self.process.stdin, self.process.stdout):
                stream.close()
