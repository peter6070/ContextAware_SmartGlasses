"""설치 없이 실행하는 Windows 배포본의 진입점."""

import argparse
from getpass import getpass
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

import serial
from serial.tools import list_ports

from software.main import main


def choose_port(device):
    ports = sorted(list_ports.comports())
    if not ports:
        raise ValueError(f"COM 포트가 없습니다. {device}의 USB 연결을 확인하세요.")
    for port in ports:
        print(f"  {port.device}  {port.description}")
    selected = input(f"{device}의 COM 포트: ").strip().upper()
    if selected not in {port.device.upper() for port in ports}:
        raise ValueError("목록에 있는 COM 포트를 입력하세요.")
    return selected


def wait_for_reply(connection, prefix, seconds, query=None):
    deadline = time.monotonic() + seconds
    next_query = 0
    while time.monotonic() < deadline:
        now = time.monotonic()
        if query and now >= next_query:
            connection.write(query)
            next_query = now + 1
        line = connection.readline().decode("ascii", errors="replace").strip()
        if line.startswith(prefix):
            return line
    return None


def setup_hotspot():
    print("글래스의 USB-UART 포트를 노트북에 연결하고 시리얼 모니터를 닫으세요.")
    with serial.Serial(choose_port("글래스"), 115200, timeout=0.25, write_timeout=2) as connection:
        if wait_for_reply(connection, "SG READY 1", 7, b"\nSG HELLO\n") != "SG READY 1":
            raise RuntimeError("글래스가 응답하지 않습니다. COM 포트와 ESP32 펌웨어 버전을 확인하세요.")
        ssid = input("2.4 GHz 핫스팟 이름: ").encode("utf-8")
        password = getpass("핫스팟 비밀번호 (개방형은 Enter): ").encode("utf-8")
        if not 1 <= len(ssid) <= 32 or (password and not 8 <= len(password) <= 63):
            raise ValueError("Wi-Fi 이름은 1~32바이트, 비밀번호는 8~63바이트여야 합니다.")
        connection.write(f"SG WIFI {ssid.hex()},{password.hex()}\n".encode("ascii"))
        reply = wait_for_reply(connection, "SG ", 4)
        if reply != "SG SAVED":
            raise RuntimeError("글래스에 설정을 저장하지 못했습니다.")
        print("글래스에 저장했습니다. 재부팅 후 핫스팟에 연결하는 중입니다.")
        stream = wait_for_reply(connection, "SG URL ", 18, b"\nSG STATUS\n")
        if stream:
            print(f"영상 주소: {stream.removeprefix('SG URL ')}")
        else:
            print("영상 주소를 받지 못했습니다. 핫스팟의 연결 기기 목록에서 확인하세요.")


def launch():
    model = next_to_executable() / "hand_landmarker.task"
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="스마트글래스 Windows 실행 파일")
        parser.add_argument("--stream", required=True, help="글래스의 MJPEG 스트림 URL")
        parser.add_argument("--serial", help="UNO의 COM 포트")
        args = parser.parse_args()
        arguments = ["--stream", args.stream, "--model", str(model)]
        if args.serial:
            arguments.extend(["--serial", args.serial])
        main(arguments)
        return 0

    try:
        mode = input("Enter: 시연 시작 / 2: 글래스 핫스팟 설정: ").strip()
        if mode == "2":
            setup_hotspot()
            input("Enter 키를 누르면 종료합니다.")
            return 0
        print("스마트글래스와 노트북을 같은 핫스팟에 연결하고 UNO를 USB로 연결하세요.")
        address = input("글래스 IP 또는 스트림 URL: ").strip()
        if "://" not in address:
            address = f"http://{address}:81/stream"
        parsed = urlsplit(address)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or " " in address:
            raise ValueError("글래스 IP 또는 스트림 URL을 확인하세요.")

        selected = choose_port("UNO")
        main(["--stream", address, "--model", str(model), "--serial", selected])
    except (OSError, RuntimeError, ValueError) as error:
        print(f"실행 오류: {error}", file=sys.stderr)
        input("Enter 키를 누르면 종료합니다.")
        return 1
    return 0


def next_to_executable():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1] / "build" / "windows"


if __name__ == "__main__":
    raise SystemExit(launch())
