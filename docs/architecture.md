# 시스템 아키텍처
## 확정된 구성
ESP32-CAM → Wi-Fi 영상 → Python PC → USB 시리얼 → Arduino UNO 호환보드 → LIGHT / CURTAIN / FAN 및 I2C LCD. PC에서 ArUco와 MediaPipe를 실행할 계획입니다. 화면 중심 선택은 카메라 방향의 근사치이며 안구 시선 추적이 아닙니다.

## 제안된 흐름과 책임
1. camera_stream은 프레임 획득과 연결 상태를 관리합니다.
2. aruco_detector는 마커 ID와 위치를 추출하고 device_selector는 설정 매핑, 중심 우선 후보, 안정화와 유지·해제를 담당합니다.
3. gesture_recognizer는 손 랜드마크와 자세를 추출하고 gesture_state_machine은 시간적 전환과 중복 방지를 담당합니다.
4. command_router는 선택 장치와 공통 명령을 장치 명령으로 변환하고 선택이 없으면 차단합니다. device_controller는 시리얼 송수신과 오류를 처리합니다.
5. config는 마커 매핑과 설정을 보관하고 main은 구성과 생명주기를 연결합니다.

마커가 잠시 사라져도 선택을 유지하고 미사용 시간 또는 해제 조건에 따라 해제합니다. 안정화 시간과 재선택 정책, 영상 전송 형식과 내부 자료형은 미확정입니다. PC와 펌웨어 시제품은 실제 하드웨어에서 아직 검증되지 않았습니다.

LCD에는 PC의 선택 정보와 Arduino의 마지막 처리 명령 상태를 표시합니다. ON/OFF는 물리적 동작의 센서 측정값이 아닙니다.

## Matter 플러그 확장 계획
노트북에 로컬 Matter 컨트롤러 어댑터를 추가하고 마커·제스처 명령을 Arduino 또는 Matter로 분기합니다. 스마트폰 앱과 별도 스마트홈 허브는 사용하지 않습니다. 최초 등록, Windows BLE, 플러그의 네트워크 방식과 LCD 표시 프로토콜은 아직 검증·구현되지 않았습니다. 구체적인 조건과 테스트는 [Matter 통합 계획](matter_integration_plan.md)에 정리합니다.
