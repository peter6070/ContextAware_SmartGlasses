"""안정된 자세 전환만 명령으로 확정합니다."""


class GestureStateMachine:
    def __init__(self, stable_seconds=0.5, cooldown_seconds=1.0):
        self.stable_seconds = stable_seconds
        self.cooldown_seconds = cooldown_seconds
        self.reset()

    def reset(self):
        self.candidate = None
        self.since = None
        self.stable = None
        self.last_command = float("-inf")

    def update(self, pose, now):
        if pose not in ("FIST", "PALM"):
            self.candidate = self.since = self.stable = None
            return None
        if pose != self.candidate:
            self.candidate, self.since = pose, now
        if now - self.since < self.stable_seconds or pose == self.stable:
            return None
        previous, self.stable = self.stable, pose
        if now - self.last_command < self.cooldown_seconds:
            return None
        command = {("FIST", "PALM"): "ACTIVATE", ("PALM", "FIST"): "DEACTIVATE"}.get((previous, pose))
        if command:
            self.last_command = now
        return command
