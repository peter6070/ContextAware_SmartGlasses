"""ArUco 마커 검출."""
import cv2


class MarkerDetector:
    def __init__(self):
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.detector = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())

    def detect(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)
        if ids is None:
            return []
        return [(int(marker_id), points.reshape(4, 2))
                for marker_id, points in zip(ids.flatten(), corners)]
