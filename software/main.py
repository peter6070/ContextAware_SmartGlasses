"""마커로 선택한 장치에 안정된 손 자세 전환 명령을 보냅니다."""
import argparse
import queue
import time
import cv2
from software.aruco_detector import MarkerDetector
from software.command_router import route
from software.config import MARKER_DEVICE_MAP
from software.device_selector import DeviceSelector
from software.device_controller import DeviceController
from software.gesture_recognizer import GestureRecognizer
from software.gesture_state_machine import GestureStateMachine


def main():
    parser = argparse.ArgumentParser(description="마커 선택과 손 제스처를 시험합니다.")
    parser.add_argument("--stream", required=True, help="ESP32-CAM MJPEG 스트림 URL")
    parser.add_argument("--model", required=True, help="MediaPipe hand_landmarker.task 경로")
    parser.add_argument("--serial", help="Arduino 포트. 생략하면 명령만 출력")
    parser.add_argument("--matter-device", help="등록된 Matter 장치 ID")
    args = parser.parse_args()
    connection = capture = recognizer = controller = matter = None
    link_ok = True
    try:
        if args.matter_device:
            from software.matter_worker import MatterWorker
            matter = MatterWorker(args.matter_device)
        if args.serial:
            import serial
            connection = serial.Serial(args.serial, 115200, timeout=1, write_timeout=1)
            time.sleep(2)
            connection.reset_input_buffer()
            controller = DeviceController(connection)
            controller.select(None)
        capture = cv2.VideoCapture(args.stream)
        if not capture.isOpened():
            raise RuntimeError("영상 스트림에 연결하지 못했습니다.")
        detector = MarkerDetector()
        recognizer = GestureRecognizer(args.model)
        selector = DeviceSelector(MARKER_DEVICE_MAP)
        state = GestureStateMachine()
        previous = None
        last_selection_sent = time.monotonic()
        while True:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("영상 수신이 중단되었습니다.")
            now = time.monotonic()
            markers = detector.detect(frame)
            pose = recognizer.recognize(frame)
            for marker_id, points in markers:
                cv2.polylines(frame, [points.astype("int32")], True, (0, 255, 0), 2)
                cv2.putText(frame, str(marker_id), tuple(points[0].astype("int32")), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            selected = selector.update(markers, frame.shape, now)
            if selected != previous:
                state.reset()
                if controller:
                    controller.select(None if selected == 'PLUG' else selected)
                    last_selection_sent = time.monotonic()
                previous = selected
            elif controller and now - last_selection_sent >= 1.0:
                controller.select(None if selected == 'PLUG' else selected)
                last_selection_sent = time.monotonic()
            action = state.update(pose, now) if selected else None
            if selected == 'PLUG' and action:
                if not matter:
                    print('Matter 장치 ID가 설정되지 않았습니다.', flush=True)
                elif not matter.submit(action):
                    print('이전 Matter 명령이 대기 중입니다.', flush=True)
            if matter:
                try:
                    while True:
                        status, result = matter.results.get_nowait()
                        print('Matter:', status, result, flush=True)
                except queue.Empty:
                    pass
            command = route(selected, action)
            if command:
                print(command, flush=True)
                if controller:
                    try:
                        print("Arduino:", controller.send(command), flush=True)
                    except RuntimeError as error:
                        print(error, flush=True)
            cv2.putText(frame, f"Device: {selected or '-'}  Hand: {pose or '-'}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow("Smart Glasses - Q to exit", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except (OSError, RuntimeError):
        link_ok = False
        raise
    finally:
        if matter is not None:
            matter.close()
        if controller is not None and link_ok:
            try:
                controller.select(None)
            except (TimeoutError, RuntimeError, OSError):
                pass
        if recognizer is not None:
            recognizer.close()
        if capture is not None:
            capture.release()
        if connection is not None:
            connection.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
