"""안정된 자세 전환만 명령으로 확정합니다."""


class GestureStateMachine:
    def __init__(self, stable_seconds=0.2, cooldown_seconds=1.0, pose_loss_seconds=0.35):
        self.stable_seconds = stable_seconds
        self.cooldown_seconds = cooldown_seconds
        self.pose_loss_seconds = pose_loss_seconds
        self.reset()

    def reset(self):
        self.candidate = None
        self.since = None
        self.stable = None
        self.lost_since = None
        self.last_command = float("-inf")

    def update(self, pose, now):
        if pose not in ("FIST", "PALM"):
            self.candidate = self.since = None
            if self.lost_since is None:
                self.lost_since = now
            return None
        if self.lost_since is not None:
            if now - self.lost_since >= self.pose_loss_seconds:
                self.stable = None
            self.lost_since = None
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
