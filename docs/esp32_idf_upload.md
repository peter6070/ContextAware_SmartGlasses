# ESP32-S3 카메라 펌웨어 업로드

스마트글래스용 ESP-IDF 프로젝트는 [firmware/esp32_cam_idf](../firmware/esp32_cam_idf)입니다. 기존 `cam_stream`에서 쓰던 ESP32-S3-N16R8과 OV2640의 핀 배치, 16 MB 플래시(DIO 80 MHz), Octal PSRAM 설정을 사용합니다. 카메라는 보드의 전용 소켓에 연결합니다.

1. ESP32 보드의 **USB-UART** 포트를 PC에 연결합니다. 장치 관리자에서 케이블을 연결했을 때 나타나는 COM 번호를 확인합니다.
2. **ESP-IDF 5.5.5 터미널**을 열고 스마트글래스 저장소의 루트 폴더에서 아래 명령을 실행합니다. `COM5`는 예시이므로 확인한 번호로 바꿉니다.

   ```powershell
   cd firmware/esp32_cam_idf
   idf.py -p COM5 -b 115200 build flash monitor
   ```

3. 시리얼 모니터를 `Ctrl+]`로 닫고, Windows 배포본의 `SmartGlasses.exe`에서 **2: 글래스 핫스팟 설정**을 선택합니다. **글래스의 COM 포트**와 2.4 GHz 핫스팟 이름·비밀번호를 입력합니다.
4. 글래스가 재부팅해 접속하면 영상 주소가 표시됩니다. 노트북을 같은 핫스팟에 연결하고 EXE를 다시 실행한 뒤, 시연 모드에서 영상 주소와 UNO의 COM 포트를 입력합니다.

Wi-Fi 설정은 글래스 내부에 저장됩니다. 핫스팟을 바꿀 때는 3단계부터 진행합니다. 기존 `main/wifi_secrets.h`는 저장된 설정이 없을 때 초기값으로 사용합니다.

`Connecting...`에서 실패하면 해당 COM 포트를 사용하는 프로그램을 닫습니다. 보드에 BOOT와 RESET 버튼이 있으면 BOOT를 누른 상태에서 RESET을 눌렀다 떼고, BOOT를 놓은 뒤 다시 실행합니다.

`Invalid head of packet`이 출력되면 플래시 중 USB-UART 통신이 끊긴 것입니다. 위 명령은 업로드 속도를 115200으로 지정합니다. 같은 증상이 계속되면 다른 USB 데이터 케이블이나 PC의 다른 USB 포트로 다시 시도합니다.
