"""화면 중심 마커의 안정 선택과 일시적 유지."""


class DeviceSelector:
    def __init__(self, mapping, dwell_seconds=1.0, hold_seconds=2.0):
        self.mapping = mapping
        self.dwell_seconds = dwell_seconds
        self.hold_seconds = hold_seconds
        self.candidate = None
        self.since = None
        self.selected = None
        self.last_seen = None

    def update(self, markers, frame_shape, now):
        height, width = frame_shape[:2]
        candidates = [(marker_id, points) for marker_id, points in markers if marker_id in self.mapping]
        if self.selected is not None and any(self.mapping[i] == self.selected for i, _ in candidates):
            self.last_seen = now
        if self.selected is not None and now - self.last_seen > self.hold_seconds:
            self.selected = None
        if not candidates:
            self.candidate = self.since = None
            return self.selected

        def distance(item):
            center = item[1].mean(axis=0)
            return ((center[0] - width / 2) ** 2 + (center[1] - height / 2) ** 2, item[0])

        marker_id = min(candidates, key=distance)[0]
        if marker_id != self.candidate:
            self.candidate, self.since = marker_id, now
        if now - self.since >= self.dwell_seconds:
            self.selected = self.mapping[marker_id]
            self.last_seen = now
        return self.selected
