"""글래스 없이 Arduino와 Matter 장치를 시험하는 수동 제어 화면."""
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from software.device_controller import DeviceController


class ArduinoService:
    """시리얼 작업을 직렬화하고 선택 상태를 주기적으로 갱신합니다."""

    def __init__(self, emit, serial_factory=None, sleep=time.sleep):
        self.emit = emit
        self.serial_factory = serial_factory
        self.sleep = sleep
        self.connection = None
        self.controller = None
        self.selected = None
        self.jobs = queue.Queue()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def submit(self, action, *args):
        self.jobs.put((action, args))

    def _disconnect(self):
        if self.connection:
            self.connection.close()
        self.connection = self.controller = None
        self.selected = None

    def _run(self):
        last_refresh = 0.0
        while True:
            try:
                action, args = self.jobs.get(timeout=0.2)
            except queue.Empty:
                action, args = 'tick', ()
            try:
                if action == 'stop':
                    try:
                        if self.controller:
                            self.controller.select(None)
                    finally:
                        self._disconnect()
                    return
                if action == 'connect':
                    self._disconnect()
                    self.emit('arduino', f'{args[0]} 연결 중…')
                    if self.serial_factory is None:
                        import serial
                        self.serial_factory = serial.Serial
                    self.connection = self.serial_factory(args[0], 115200, timeout=1, write_timeout=1)
                    self.sleep(2)
                    self.connection.reset_input_buffer()
                    self.controller = DeviceController(self.connection)
                    self.controller.select(None)
                    self.emit('arduino', f'{args[0]} 연결됨')
                elif action == 'disconnect':
                    if self.controller:
                        self.controller.select(None)
                    self._disconnect()
                    self.emit('arduino', '연결 안 됨')
                elif action in ('select', 'command'):
                    if not self.controller:
                        raise RuntimeError('먼저 Arduino를 연결해 주세요.')
                    device = args[0]
                    self.controller.select(device)
                    self.selected = device
                    last_refresh = time.monotonic()
                    if action == 'command':
                        self.controller.send(args[1])
                        self.emit('log', f'Arduino 명령 처리: {args[1]} (실제 동작 확인 필요)')
                    else:
                        self.emit('log', f'LCD 표시 선택: {device or "NONE"}')
                elif action == 'tick' and self.controller and self.selected and time.monotonic() - last_refresh >= 1:
                    self.controller.select(self.selected)
                    last_refresh = time.monotonic()
            except (OSError, RuntimeError, ValueError) as error:
                self.emit('log', str(error))
                if action == 'stop':
                    return
                if action == 'connect':
                    self._disconnect()
                    self.emit('arduino', '연결 실패 — 아래 처리 결과 확인')
                    if isinstance(error, TimeoutError):
                        self.emit('log', '포트는 열렸지만 UNO가 응답하지 않습니다. 올바른 스케치를 업로드했는지 확인하세요.')
                    continue
                # 응답 유실 또는 끊김은 후속 응답이 섞일 수 있으므로 재연결이 필요합니다.
                if isinstance(error, OSError):
                    self._disconnect()
                    self.emit('arduino', '연결 오류 — 다시 연결해 주세요')
            except Exception as error:
                self._disconnect()
                self.emit('arduino', '연결 오류 — 다시 연결해 주세요')
                self.emit('log', f'시리얼 오류: {error}')
                if action == 'stop':
                    return


class MatterService:
    """Matter 등록과 명령은 화면 스레드에서 실행하지 않습니다."""

    def __init__(self, emit):
        self.emit = emit
        self.jobs = queue.Queue()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def submit(self, action, *args):
        self.jobs.put((action, args))

    def _run(self):
        from software.matter_controller import MatterController
        controller = None
        try:
            while True:
                action, args = self.jobs.get()
                if action == 'stop':
                    return
                try:
                    if controller is None:
                        controller = MatterController()
                    if action == 'register':
                        code, ssid, password = args
                        result = controller.request('commission', timeout=180, code=code, ssid=ssid, password=password)
                        self.emit('log', f'Matter 등록 완료: {result["id"]}')
                        action = 'list'
                    if action == 'list':
                        self.emit('devices', controller.request('list')['devices'])
                    elif action in ('on', 'off', 'status'):
                        result = controller.request(action, id=args[0])
                        self.emit('log', f'Matter {action}: 요청 처리됨. 캐시 상태: {result.get("cachedState")} (실제 상태 미확인)')
                except (OSError, RuntimeError, ValueError) as error:
                    self.emit('log', f'Matter 오류: {error}')
                    if isinstance(error, OSError) and controller:
                        controller.close()
                        controller = None
                except Exception as error:
                    self.emit('log', f'Matter 처리 실패: {type(error).__name__}')
                    if controller:
                        controller.close()
                        controller = None
        finally:
            if controller:
                controller.close()


class ManualControlApp:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.arduino = ArduinoService(self.emit)
        self.matter = MatterService(self.emit)
        self.arduino_status = tk.StringVar(value='연결 안 됨')
        self.port = tk.StringVar()
        self.device = tk.StringVar()
        self.code = tk.StringVar()
        self.ssid = tk.StringVar()
        self.password = tk.StringVar()
        root.title('스마트글래스 수동 제어')
        root.geometry('680x700')
        root.minsize(600, 620)
        root.protocol('WM_DELETE_WINDOW', self.close)
        self._build()
        self.refresh_ports()
        root.after(100, self._drain)

    def emit(self, kind, value):
        self.events.put((kind, value))

    def _build(self):
        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='수동 제어', font=('맑은 고딕', 17, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='카메라 없이 보드와 플러그를 시험합니다.').pack(anchor='w', pady=(0, 10))

        arduino = ttk.LabelFrame(frame, text='Arduino 연결', padding=10)
        arduino.pack(fill='x', pady=4)
        line = ttk.Frame(arduino)
        line.pack(fill='x')
        self.ports = ttk.Combobox(line, textvariable=self.port, width=14)
        self.ports.pack(side='left')
        ttk.Button(line, text='포트 검색', command=self.refresh_ports).pack(side='left', padx=4)
        ttk.Button(line, text='연결', command=self.connect_arduino).pack(side='left', padx=4)
        ttk.Button(line, text='연결 해제', command=lambda: self.arduino.submit('disconnect')).pack(side='left')
        ttk.Label(arduino, textvariable=self.arduino_status).pack(anchor='w', pady=(6, 0))

        controls = ttk.LabelFrame(frame, text='LED · 커튼 서보 · 팬 스텝모터', padding=10)
        controls.pack(fill='x', pady=4)
        for label, device, on_label, on_cmd, off_label, off_cmd in [
            ('조명', 'LIGHT', '켜기', 'LIGHT,ON', '끄기', 'LIGHT,OFF'),
            ('커튼', 'CURTAIN', '열기', 'CURTAIN,OPEN', '닫기', 'CURTAIN,CLOSE'),
            ('팬', 'FAN', '시작', 'FAN,START', '정지', 'FAN,STOP'),
        ]:
            row = ttk.Frame(controls)
            row.pack(fill='x', pady=2)
            ttk.Label(row, text=label, width=10).pack(side='left')
            ttk.Button(row, text=on_label, command=lambda d=device, c=on_cmd: self.arduino.submit('command', d, c)).pack(side='left', padx=3)
            ttk.Button(row, text=off_label, command=lambda d=device, c=off_cmd: self.arduino.submit('command', d, c)).pack(side='left', padx=3)

        lcd = ttk.LabelFrame(frame, text='LCD 표시 대상 선택', padding=10)
        lcd.pack(fill='x', pady=4)
        for name, device in [('조명', 'LIGHT'), ('커튼', 'CURTAIN'), ('팬', 'FAN'), ('선택 해제', None)]:
            ttk.Button(lcd, text=name, command=lambda d=device: self.arduino.submit('select', d)).pack(side='left', padx=3)
        ttk.Label(lcd, text='LCD의 CMD는 실제 센서값이 아닌 명령 상태입니다.').pack(anchor='w', pady=(5, 0))

        matter = ttk.LabelFrame(frame, text='Matter 플러그', padding=10)
        matter.pack(fill='x', pady=4)
        row = ttk.Frame(matter)
        row.pack(fill='x')
        self.devices = ttk.Combobox(row, textvariable=self.device, width=20)
        self.devices.pack(side='left')
        ttk.Button(row, text='기기 조회', command=lambda: self.matter.submit('list')).pack(side='left', padx=3)
        for label, action in [('켜기', 'on'), ('끄기', 'off'), ('상태', 'status')]:
            ttk.Button(row, text=label, command=lambda a=action: self.matter_action(a)).pack(side='left', padx=3)
        ttk.Button(matter, text='새 플러그 등록', command=self.registration).pack(anchor='w', pady=(6, 0))

        ttk.Label(frame, text='처리 결과').pack(anchor='w', pady=(8, 2))
        self.log = tk.Text(frame, height=6, wrap='word', state='disabled')
        self.log.pack(fill='both', expand=True)

    def refresh_ports(self):
        try:
            from serial.tools import list_ports
            ports = [port.device for port in list_ports.comports()]
            self.ports['values'] = ports
            if len(ports) == 1:
                self.port.set(ports[0])
            elif len(ports) > 1:
                detected = [p.device for p in list_ports.comports() if p.vid in (0x2341, 0x2A03)]
                if len(detected) == 1:
                    self.port.set(detected[0])
        except ImportError:
            self.emit('log', 'pyserial이 설치되지 않았습니다.')

    def connect_arduino(self):
        if not self.port.get().strip():
            self.emit('log', 'Arduino 포트를 선택해 주세요.')
            return
        self.arduino.submit('connect', self.port.get().strip())

    def matter_action(self, action):
        device = self.device.get().strip()
        if not device:
            self.emit('log', '먼저 Matter 기기를 조회하고 선택해 주세요.')
            return
        self.matter.submit(action, device)

    def registration(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('Matter 플러그 등록')
        dialog.transient(self.root)
        box = ttk.Frame(dialog, padding=16)
        box.pack(fill='both', expand=True)
        for index, (label, var, secret) in enumerate([
            ('Matter 숫자 코드', self.code, True), ('Wi-Fi 이름', self.ssid, False), ('Wi-Fi 비밀번호', self.password, True)
        ]):
            ttk.Label(box, text=label).grid(row=index, column=0, sticky='w', pady=5)
            ttk.Entry(box, textvariable=var, show='*' if secret else '', width=32).grid(row=index, column=1, padx=8, pady=5)

        def start():
            code = self.code.get().strip().replace('-', '')
            ssid = self.ssid.get().strip()
            password = self.password.get()
            self.code.set('')
            self.password.set('')
            if not code.isdigit() or not ssid:
                self.emit('log', 'Matter 숫자 코드와 Wi-Fi 이름을 확인해 주세요.')
                return
            self.matter.submit('register', code, ssid, password)
            self.emit('log', 'Matter 등록 중입니다. 시간이 걸릴 수 있습니다.')
            dialog.destroy()

        ttk.Label(box, text='플러그를 등록 모드로 둔 후 직접 입력해 주세요.').grid(row=3, columnspan=2, sticky='w')
        ttk.Button(box, text='등록', command=start).grid(row=4, columnspan=2, pady=(10, 0))

    def _drain(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'arduino':
                    self.arduino_status.set(value)
                elif kind == 'devices':
                    ids = [item['id'] for item in value]
                    self.devices['values'] = ids
                    if len(ids) == 1:
                        self.device.set(ids[0])
                    self._log(f'Matter 등록 기기: {len(ids)}개')
                else:
                    self._log(value)
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', str(text) + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def close(self):
        self.arduino.submit('stop')
        self.matter.submit('stop')
        self.root.destroy()


def main():
    root = tk.Tk()
    ManualControlApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
