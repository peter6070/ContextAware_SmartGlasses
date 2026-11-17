"""공통 명령을 장치 명령으로 변환합니다."""
COMMANDS = {
    "LIGHT": {"ACTIVATE": "LIGHT,ON", "DEACTIVATE": "LIGHT,OFF"},
    "CURTAIN": {"ACTIVATE": "CURTAIN,OPEN", "DEACTIVATE": "CURTAIN,CLOSE"},
    "FAN": {"ACTIVATE": "FAN,START", "DEACTIVATE": "FAN,STOP"},
}


def route(device, action):
    return COMMANDS.get(device, {}).get(action)
