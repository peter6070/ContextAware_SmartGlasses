# Context-Aware Smart Glasses

ESP32-CAM 영상의 ArUco 마커로 장치를 선택하고 손 제스처로 미니어처 스마트룸을 제어하는 프로젝트입니다. 현재 PC 인식 시제품을 작성했으며 실제 스트리밍 및 장치 구동은 아직 검증되지 않았습니다.

ESP32-CAM → Wi-Fi 영상 → Python PC → USB 시리얼 → Arduino UNO 호환보드 → 조명·커튼·환기. 화면 중심 선택은 실제 시선 추적이 아닙니다.

## 개발 환경
Python 가상환경을 만들고 의존성을 설치합니다. 버전과 호환성은 실제 환경에서 확인 후 고정합니다. Arduino IDE와 ESP32 보드 패키지는 보드 모델 확인 후 설정합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m software.main --help
```

실행에는 아래 PC 인식 시제품 절의 인자가 필요합니다. [개요](docs/project_overview.md), [아키텍처](docs/architecture.md), [제스처](docs/gesture_design.md), [통신](docs/communication_protocol.md), [로드맵](docs/development_roadmap.md), [부품](hardware/components.md), [배선](hardware/wiring.md)을 참고하십시오.

## 글래스 없이 수동 제어

프로젝트 루트에서 `python -m software.manual_control`을 실행합니다. Arduino 포트를 검색해 연결하면 조명 켜기·끄기, 커튼 열기·닫기, 팬 시작·정지를 누를 수 있습니다. LCD의 표시 장치는 별도 버튼으로 선택합니다. LCD는 선택된 장치와 마지막 명령을 표시하며 임의의 문자 입력이나 실제 작동 감지는 지원하지 않습니다.

Matter 영역에서 등록된 기기를 조회하고 켜기·끄기를 요청하거나, 새 기기 등록 화면에서 설정 코드와 Wi-Fi 정보를 직접 입력할 수 있습니다. 최초 등록에는 Node.js 의존성과 Bluetooth가 필요하며, 플러그가 응답하지 않으면 오류가 표시됩니다. Matter의 표시 상태는 캐시이며 실제 상태를 보장하지 않습니다. Arduino 출력과 LCD는 배선·부품 확인 전 펌웨어에서 기본 비활성화되어 있습니다. 실제 보드 및 플러그 연결 시험은 아직 하지 않았습니다.

노트북에서 헤이홈 플러그 Air를 앱이나 별도 스마트홈 허브 없이 직접 제어하는 기능은 [Matter 통합 계획](docs/matter_integration_plan.md)에 설계되어 있습니다. 등록·제어 시제품을 작성했으며 실장치 등록과 네트워크 이동은 아직 검증하지 않았습니다.

## PC 인식 시제품

PC에서 OpenCV ArUco DICT_4X4_50 마커를 검출해 1초 안정적으로 보인 화면 중심 장치를 선택합니다. 마커가 사라지면 2초간 선택을 유지합니다. 선택 후 주먹→손바닥은 활성화, 손바닥→주먹은 비활성화 명령입니다. 임계값은 임시값이며 실제 영상에서 검증하지 않았습니다. 핀치 조절은 아직 구현되지 않았습니다.

MediaPipe Hand Landmarker의 호환되는 모델 파일을 준비한 뒤 다음과 같이 실행합니다. 스트림은 MJPEG URL입니다. 실제 주소와 경로로 바꾸세요.
```powershell
python -m software.main --stream http://<ESP32주소>:81/stream --model <모델파일경로>
```
기본적으로 명령은 출력만 합니다. `--serial COM포트`를 추가하면 115200 baud로 줄바꿈 명령을 보냅니다. Arduino 수신 및 조명·커튼 서보·팬 스텝모터 제어 코드는 작성했으나 변경된 코드의 실장치 동작은 검증 전입니다. ESP32 영상 코드도 후보 핀 배치를 사용하므로 보드 확인이 필요합니다.

## 하드웨어 시제품 설정
보내주신 상품과 동일한 보드인지 아직 확인되지 않았습니다. ESP32 코드는 [Freenove ESP32-S3 WROOM 카메라 예제](https://github.com/Freenove/Freenove_ESP32_S3_WROOM_Board/blob/main/C/Sketches/Sketch_07.2_As_VideoWebServer/Sketch_07.2_As_VideoWebServer.ino)의 ESP32S3_EYE 핀 배치를 후보로 사용합니다. 실제 보드가 일치하는지 확인한 후 `firmware/esp32_cam/wifi_secrets.example.h`를 같은 폴더에 `wifi_secrets.h`로 복사하고 Wi-Fi 정보를 입력한 뒤 확인 매크로의 주석을 해제합니다. ESP32-S3용 Arduino 보드 패키지와 보드에 맞는 설정이 필요합니다. 업로드 후 시리얼 모니터 115200 baud에서 출력된 스트림 주소를 PC에 입력합니다. 인증 정보 파일은 Git에서 제외됩니다.

초록색 LED는 D3, 팬용 28BYJ-48 스텝모터 드라이버의 IN1~IN4는 D10~D13에 연결했습니다. 커튼 서보 신호는 D9로 계획하며 실제 배선은 확인이 필요합니다. LED 극성과 전류 제한, 모터 전원과 공통 접지는 실물 확인이 필요합니다. `LIGHT_ACTIVE_HIGH`와 서보의 열림·닫힘 각도는 시험용 설정입니다. 서보를 기구에 연결하기 전 방향과 이동 범위를 확인하세요.

MediaPipe 모델은 [공식 Hand Landmarker 안내](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)에서 내려받습니다. 실제 입력 영상에서 제스처 정확도와 오작동은 검증되지 않았으며, 실물 배선과 영상 수신도 아직 시험하지 않았습니다.

## 팬과 LCD 시제품
- FAN은 ULN2003 드라이버의 IN1~IN4와 D10~D13으로 28BYJ-48 스텝모터를 구동합니다. 모터용 5V 전원과 공통 접지를 확인합니다. 속도 조절은 미구현입니다.
- LCD는 HD44780 호환 16×2 I2C 문자 LCD를 **가정**합니다. Arduino IDE 라이브러리 관리자에서 [hd44780 라이브러리](https://github.com/duinoWitchery/hd44780)를 설치합니다. 실제 LCD 모델·전압·크기와 호환되는 I2C 백팩을 확인한 후 `LCD_CONFIRMED`를 활성화합니다. 일반 UNO R3의 SDA/SCL은 A4/A5이지만 사용 중인 호환보드의 핀을 확인해야 합니다.
- LCD 1행은 `SEL:LIGHT`처럼 선택 장치, 2행은 `CMD:ON`, `CMD:OFF`, `CMD:--`를 표시합니다. CURTAIN의 ON/OFF는 OPEN/CLOSE 명령 상태입니다. 센서 피드백이 없으므로 이 값은 실제 동작·위치가 아니라 **마지막 처리 명령 상태**이며 초기 상태를 모르면 --로 표시합니다.
- PC는 선택 정보를 1초마다 Arduino에 전송합니다. 약 3초 동안 갱신되지 않으면 선택을 해제하고 LCD에 NONE을 표시합니다. 연결이 끊겨도 기존 출력은 유지되며 물리적 자동 정지는 구현되지 않았습니다.

## Matter 플러그 시제품

Node.js와 프로젝트 의존성이 필요합니다. 설치가 필요하면 저장소 루트에서 `npm ci --prefix matter_adapter`를 실행합니다. Windows의 BLE 어댑터와 Matter 플러그가 페어링 가능한 상태여야 합니다. 최초 등록은 로컬 터미널에서 실행합니다.

```powershell
python -m software.matter_setup register
python -m software.matter_setup list
```

코드와 Wi-Fi 비밀번호는 프롬프트에 직접 입력합니다. 명령행 인자나 채팅에 입력하지 마세요. 등록이 성공하면 표시되는 장치 ID를 사용하여 기존 실행 명령에 `--matter-device 장치ID`를 추가합니다. [마커 4](assets/aruco_markers/marker_4.png)를 인식해 선택한 뒤 주먹→손바닥은 켜기, 반대 전환은 끄기입니다. `python -m software.matter_setup status --device 장치ID`로 상태를 요청할 수 있으나 현재 상태값은 캐시이며 실시간 확인을 보장하지 않습니다.

Windows BLE 및 실제 플러그 등록, 기기 On/Off, 네트워크 변경·공공망·핫스팟, LCD Matter 표시는 아직 검증하거나 완성하지 않았습니다. 네트워크 장애 시 제어가 실패할 수 있습니다. 이미 전송된 명령은 선택이 바뀌어도 취소할 수 없습니다.
