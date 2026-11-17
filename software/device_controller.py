"""Arduino와 한 번에 한 명령을 교환합니다."""


class DeviceController:
    def __init__(self, connection):
        self.connection = connection

    def send(self, command):
        self.connection.write((command + "\n").encode("ascii"))
        response = self.connection.readline().decode("ascii", errors="replace").strip()
        if not response:
            # 지연된 응답을 다음 명령의 응답으로 오인하지 않도록 사용을 중단합니다.
            raise TimeoutError(f"Arduino 응답 시간 초과: {command}")
        if response != "OK":
            raise RuntimeError(f"Arduino 명령 실패: {command}: {response}")
        return response

    def select(self, device):
        if device not in (None, "LIGHT", "CURTAIN", "FAN"):
            raise ValueError("지원하지 않는 장치입니다.")
        return self.send("SELECT," + (device or "NONE"))
