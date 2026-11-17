# Python–Arduino 시리얼 통신
## 확정된 사항
PC와 Arduino UNO 호환보드는 USB 시리얼로 연결할 계획입니다. 장치 선택이 없는 명령은 전송하지 않습니다. 아래 시제품 규격을 구현했으며 실장치 검증은 아직 하지 않았습니다.

## 프로토콜 제안
UTF-8의 ASCII 부분집합, 줄바꿈으로 구분한 텍스트 명령을 후보로 둡니다. 형식은 DEVICE,ACTION[,VALUE], VALUE는 0~100 정수로 제안합니다. 예: LIGHT,ON / CURTAIN,OPEN / LIGHT,SET,50 / FAN,STOP. SET은 밝기·열림 정도·조건부 속도를 뜻합니다. 나머지 명령은 LIGHT ON/OFF, CURTAIN OPEN/CLOSE, FAN START/STOP입니다.

응답 후보는 OK 또는 ERR,<사유코드> 한 줄입니다. 미지원 장치·동작, 잘못된 값과 형식은 실행하지 않고 오류를 반환하도록 제안합니다. 포트, 전송 속도, 타임아웃, 재연결, 응답 상관관계와 중복 전송 정책은 미정입니다. 응답 유실 시 재시도가 중복 동작을 만들 수 있으므로 구현 전 멱등성 또는 식별자 정책을 정해야 합니다.

## 시제품 구현 상태
115200 baud, ASCII 줄바꿈 명령을 사용합니다. PC는 `SELECT,LIGHT`, `SELECT,CURTAIN`, `SELECT,FAN`, `SELECT,NONE`으로 선택 상태를 전송하고 1초마다 갱신합니다. Arduino는 약 3초 동안 갱신되지 않으면 선택을 해제합니다. 출력 자체는 유지됩니다.

선택된 장치에 LIGHT,ON/OFF, CURTAIN,OPEN/CLOSE, FAN,START/STOP을 처리합니다. 선택 불일치나 미설정 출력은 ERR 응답을 반환하며, SET은 아직 미구현입니다. 출력 없이 선택 상태만 바꿀 수 있습니다. PC는 명령별 OK를 기다리고 응답 시간 초과 시 통신을 중단하여 뒤늦은 응답을 다음 명령의 응답으로 오인하지 않습니다. 재시도는 하지 않습니다.

LCD는 선택 장치와 마지막 처리 명령 상태를 표시합니다. OK와 LCD의 ON/OFF는 실제 부품 동작을 측정하거나 보증하지 않습니다.
