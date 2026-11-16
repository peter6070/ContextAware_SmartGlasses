# Context-Aware Smart Glasses

ESP32-CAM 영상의 ArUco 마커로 장치를 선택하고 손 제스처로 미니어처 스마트룸을 제어하는 프로젝트입니다. 현재 Phase 1이며 영상, 인식, 통신 및 장치 구동은 구현되지 않았습니다.

ESP32-CAM → Wi-Fi 영상 → Python PC → USB 시리얼 → Arduino UNO 호환보드 → 조명·커튼·환기. 화면 중심 선택은 실제 시선 추적이 아닙니다.

## 개발 환경
Python 가상환경을 만들고 의존성을 설치합니다. 버전과 호환성은 실제 환경에서 확인 후 고정합니다. Arduino IDE와 ESP32 보드 패키지는 보드 모델 확인 후 설정합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m software.main
```

진입점은 미구현 상태를 알리고 종료합니다. [개요](docs/project_overview.md), [아키텍처](docs/architecture.md), [제스처](docs/gesture_design.md), [통신](docs/communication_protocol.md), [로드맵](docs/development_roadmap.md), [부품](hardware/components.md), [배선](hardware/wiring.md)을 참고하십시오.
