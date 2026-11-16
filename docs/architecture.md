# 시스템 아키텍처
## 확정된 구성
ESP32-CAM → Wi-Fi 영상 → Python PC → USB 시리얼 → Arduino UNO 호환보드 → LIGHT / CURTAIN / FAN. PC에서 ArUco와 MediaPipe를 실행할 계획입니다. 화면 중심 선택은 카메라 방향의 근사치이며 안구 시선 추적이 아닙니다.

## 제안된 흐름과 책임
1. camera_stream은 프레임 획득과 연결 상태를 관리합니다.
2. aruco_detector는 마커 ID와 위치를 추출하고 device_selector는 설정 매핑, 중심 우선 후보, 안정화와 유지·해제를 담당합니다.
3. gesture_recognizer는 손 랜드마크와 자세를 추출하고 gesture_state_machine은 시간적 전환과 중복 방지를 담당합니다.
4. command_router는 선택 장치와 공통 명령을 장치 명령으로 변환하고 선택이 없으면 차단합니다. device_controller는 시리얼 송수신과 오류를 처리합니다.
5. config는 마커 매핑과 설정을 보관하고 main은 구성과 생명주기를 연결합니다.

마커가 잠시 사라져도 선택을 유지하고 미사용 시간 또는 해제 조건에 따라 해제합니다. 안정화 시간과 재선택 정책, 영상 전송 형식과 내부 자료형은 미확정입니다. 모든 모듈은 골격입니다.
