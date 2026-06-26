import os
import threading
from typing import List

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit
from src.utils.paths import resource_path


# Score threshold for YuNet face detection (0.0–1.0).
# Lower values recall more faces at the cost of precision.
_YUNET_SCORE_THRESH = 0.60
_YUNET_NMS_THRESH   = 0.30
_YUNET_TOP_K        = 5000


def _load_yunet(model_path: str, input_size: tuple) -> cv2.FaceDetectorYN:
    """Instantiate a YuNet FaceDetectorYN for the given input resolution."""
    return cv2.FaceDetectorYN.create(
        model=model_path,
        config="",
        input_size=input_size,
        score_threshold=_YUNET_SCORE_THRESH,
        nms_threshold=_YUNET_NMS_THRESH,
        top_k=_YUNET_TOP_K,
    )


class VisionDetector(BaseDetector):
    def __init__(self, mode: str = "faces", identity_manager=None):
        self.mode = mode
        self.identity_manager = identity_manager
        self._local = threading.local()

        if self.mode == "bodies":
            model_path = resource_path("assets/efficientdet_lite2.tflite")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Missing body model: {model_path}")

            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            fd_val = float(settings.value("model_face_detect", 0.20))

            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=fd_val, max_results=5
            )
            print(f"[DEBUG] Initializing ObjectDetector with dynamic threshold: {fd_val:.2f}")
            self.detector = vision.ObjectDetector.create_from_options(options)

        elif self.mode == "faces":
            yunet_path = resource_path("assets/face_detection_yunet_2023mar.onnx")
            if not os.path.exists(yunet_path):
                raise FileNotFoundError(
                    f"Missing YuNet model: {yunet_path}\n"
                    "Download it with:\n"
                    "  curl -L -o assets/face_detection_yunet_2023mar.onnx "
                    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
                    "face_detection_yunet_2023mar.onnx"
                )
            # YuNet detector is created per-call with the actual image size, but
            # we store the model path for thread-local instantiation.
            self._yunet_model_path = yunet_path

    def _get_yunet(self, width: int, height: int) -> cv2.FaceDetectorYN:
        """Return a thread-local YuNet instance, re-created when input size changes."""
        detector = getattr(self._local, "yunet", None)
        last_size = getattr(self._local, "yunet_size", None)

        if detector is None or last_size != (width, height):
            detector = _load_yunet(self._yunet_model_path, (width, height))
            self._local.yunet = detector
            self._local.yunet_size = (width, height)

        return detector

    def detect(self, image_path: str, match_identities: bool = True) -> List[SensitiveHit]:
        abs_path = os.path.abspath(image_path)
        cv_image = cv2.imread(abs_path)
        if cv_image is None:
            return []

        hits = []

        if self.mode == "text":
            return []

        if self.mode == "faces":
            hits = self._detect_faces(cv_image, match_identities)

        elif self.mode == "bodies":
            hits = self._detect_bodies(cv_image)

        return hits

    def _detect_faces(self, cv_image: np.ndarray, match_identities: bool) -> List[SensitiveHit]:
        """Run YuNet face detection and optionally match identities via SFace/LBPH."""
        h_img, w_img = cv_image.shape[:2]

        yunet = self._get_yunet(w_img, h_img)

        # YuNet expects BGR input directly (no grayscale conversion needed).
        _, detections = yunet.detect(cv_image)

        hits = []
        if detections is None:
            return hits

        for det in detections:
            # Each detection row: [x, y, w, h, <landmarks x5>, score]
            x, y, w, h = int(det[0]), int(det[1]), int(det[2]), int(det[3])
            score = float(det[-1])

            # Clamp to image bounds.
            x = max(0, x)
            y = max(0, y)
            w = min(w_img - x, w)
            h = min(h_img - y, h)

            if w <= 0 or h <= 0:
                continue

            identity = None
            if self.identity_manager and match_identities:
                face_crop = cv_image[y:y + h, x:x + w]
                if face_crop.size > 0:
                    identity = self.identity_manager.match_face(face_crop)

            label = f"FACE: {identity}" if identity else "FACE"
            hits.append(
                SensitiveHit(
                    x=x, y=y, w=w, h=h,
                    label=label,
                    confidence=score,
                    identity=identity or "",
                )
            )

        return hits

    def _detect_bodies(self, cv_image: np.ndarray) -> List[SensitiveHit]:
        """Run MediaPipe EfficientDet-Lite2 body/person detection."""
        from PySide6.QtCore import QSettings
        settings = QSettings("SafeMARC", "SafeMARC")
        fd_val = float(settings.value("model_face_detect", 0.20))

        if not hasattr(self, "_active_fd_val") or self._active_fd_val != fd_val:
            print(f"[DEBUG] Recreating ObjectDetector with active threshold: {fd_val:.2f}")
            self._active_fd_val = fd_val
            model_path = resource_path("assets/efficientdet_lite2.tflite")
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=fd_val, max_results=5
            )
            self.detector = vision.ObjectDetector.create_from_options(options)

        adjusted = cv2.convertScaleAbs(cv_image, alpha=1.5, beta=10)
        rgb_image = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        result = self.detector.detect(mp_image)

        hits = []
        if result and result.detections:
            for detection in result.detections:
                bbox = detection.bounding_box
                cat = detection.categories[0]
                if cat.category_name in ["person", "face"]:
                    hits.append(
                        SensitiveHit(
                            x=int(bbox.origin_x),
                            y=int(bbox.origin_y),
                            w=int(bbox.width),
                            h=int(bbox.height),
                            label="BODY",
                            confidence=float(cat.score),
                        )
                    )
        return hits

    def cleanup(self):
        if hasattr(self, "detector") and self.detector:
            try:
                self.detector.close()
            except Exception:
                pass
