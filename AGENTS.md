# AGENTS.md

## Project

Context-Aware Smart Glasses

ESP32-CAM, OpenCV ArUco, MediaPipe, Arduino를 활용하는 스마트글래스 기반 상황 인식형 제스처 인터페이스.

목표: 대학 전공 학술제에서 시연 가능한 미니어처 스마트홈 제어 시스템 개발.

## Instructions

- 모든 설명과 문서는 한국어로 작성합니다. 코드 식별자는 영어를 사용합니다.
- 작업 전 관련 설계 문서와 필요한 Skill을 확인합니다.
- 작업과 무관한 Skill은 읽지 않습니다.
- 확인되지 않은 사항을 임의로 확정하지 않습니다.
- 요청된 작업 범위만 수정하고, 검증 결과를 정확히 보고합니다.

## Skills

상세 규칙은 `.agents/skills/`에서 관리합니다.

| 작업 유형 | Skill |
|---|---|
| 회로, 배선, 전원, 부품 | `hardware` |
| ArUco, MediaPipe, 제스처 인식 | `computer-vision` |
| ESP32-CAM, Arduino 펌웨어 | `firmware` |
| Python 구조, 통신, 명령 처리 | `python-development` |
| 테스트, 성능 측정, 검증 | `testing` |
| README, 설계 문서, 개발 기록 | `documentation` |

각 Skill의 `SKILL.md`에 있는 YAML `description`을 기준으로 관련성을 판단합니다.

작업에 필요한 Skill만 읽고 적용합니다. 복합 작업에서는 관련 Skill을 함께 사용합니다.

## References

- 프로젝트 요구사항: `docs/project_overview.md`
- 시스템 아키텍처: `docs/architecture.md`
- 제스처 설계: `docs/gesture_design.md`
- 통신 규격: `docs/communication_protocol.md`
- 개발 현황: `docs/development_roadmap.md`

필요한 문서만 확인합니다.

## Completion

작업 완료 시 변경 파일, 테스트 결과, 미완료 항목을 간결하게 보고합니다.