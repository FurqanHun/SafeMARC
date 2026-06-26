import os
import threading
from typing import List, Optional

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit
from src.utils.paths import resource_path


_YUNET_SCORE_THRESH = 0.70   # Higher threshold reduces lip/eye false positives.
_YUNET_NMS_THRESH   = 0.30
_YUNET_TOP_K        = 5000

# Downscale images wider/taller than this before the large-face detection pass.
_LARGE_FACE_MAX_DIM = 640


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
                    "Download with:\n"
                    "  curl -L -o assets/face_detection_yunet_2023mar.onnx "
                    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
                    "face_detection_yunet_2023mar.onnx"
                )
            self._yunet_model_path = yunet_path

    # ------------------------------------------------------------------
    # Thread-local YuNet instances (keyed by input size)
    # ------------------------------------------------------------------

    def _get_yunet(self, w: int, h: int) -> cv2.FaceDetectorYN:
        """Native-resolution thread-local YuNet, re-created when size changes."""
        if (getattr(self._local, "yunet", None) is None
                or getattr(self._local, "yunet_size", None) != (w, h)):
            self._local.yunet = _load_yunet(self._yunet_model_path, (w, h))
            self._local.yunet_size = (w, h)
        return self._local.yunet

    def _get_yunet_small(self, w: int, h: int) -> cv2.FaceDetectorYN:
        """Downscaled-pass thread-local YuNet instance."""
        if (getattr(self._local, "yunet_small", None) is None
                or getattr(self._local, "yunet_small_size", None) != (w, h)):
            self._local.yunet_small = _load_yunet(self._yunet_model_path, (w, h))
            self._local.yunet_small_size = (w, h)
        return self._local.yunet_small

    # ------------------------------------------------------------------
    # Multi-scale detection + NMS
    # ------------------------------------------------------------------

    def _multi_scale_detect(self, cv_image: np.ndarray, w_img: int, h_img: int) -> list:
        """
        Run YuNet at native resolution, then at a downscaled resolution when
        the image is large (catches portrait-sized faces > 300px which YuNet's
        training range doesn't cover at native scale).  Results are merged with
        containment-aware NMS.
        """
        all_dets = []

        # Pass 1: native resolution — catches small/medium faces.
        yunet = self._get_yunet(w_img, h_img)
        _, dets = yunet.detect(cv_image)
        if dets is not None:
            all_dets.extend(dets.tolist())

        # Pass 2: downscaled — catches large faces (portraits, close-ups).
        if max(w_img, h_img) > _LARGE_FACE_MAX_DIM:
            scale = _LARGE_FACE_MAX_DIM / max(w_img, h_img)
            sw = max(1, int(w_img * scale))
            sh = max(1, int(h_img * scale))
            small = cv2.resize(cv_image, (sw, sh), interpolation=cv2.INTER_AREA)

            yunet_s = self._get_yunet_small(sw, sh)
            _, dets_s = yunet_s.detect(small)
            if dets_s is not None:
                for d in dets_s.tolist():
                    d_up = list(d)
                    # Scale bbox + 5 landmarks (indices 0-13) back to original coords.
                    for i in range(14):
                        d_up[i] = d_up[i] / scale
                    all_dets.append(d_up)

        return self._nms(all_dets)

    def _nms(self, detections: list, iou_thresh: float = 0.40) -> list:
        """
        Greedy NMS sorted by confidence.  Uses containment ratio instead of
        pure IoU so that sub-face detections (lips, eyes) inside a larger face
        box are suppressed even when their IoU with the face box is low.
        """
        if not detections:
            return []

        dets = sorted(detections, key=lambda d: float(d[-1]), reverse=True)
        kept = []

        for det in dets:
            bx, by, bw, bh = det[0], det[1], det[2], det[3]
            suppressed = False
            for k in kept:
                kx, ky, kw, kh = k[0], k[1], k[2], k[3]
                ix = max(bx, kx);  iy = max(by, ky)
                iw = min(bx + bw, kx + kw) - ix
                ih = min(by + bh, ky + kh) - iy
                if iw > 0 and ih > 0:
                    inter = iw * ih
                    # Suppress if the smaller box is mostly inside the larger one.
                    min_area = min(bw * bh, kw * kh)
                    if inter / max(min_area, 1) > iou_thresh:
                        suppressed = True
                        break
            if not suppressed:
                kept.append(det)

        return kept

    # ------------------------------------------------------------------
    # Public detect
    # ------------------------------------------------------------------

    def detect(self, image_path: str, match_identities: bool = True) -> List[SensitiveHit]:
        abs_path = os.path.abspath(image_path)
        cv_image = cv2.imread(abs_path)
        if cv_image is None:
            return []

        if self.mode == "text":
            return []
        if self.mode == "faces":
            return self._detect_faces(cv_image, match_identities)
        if self.mode == "bodies":
            return self._detect_bodies(cv_image)
        return []

    def _detect_faces(self, cv_image: np.ndarray, match_identities: bool) -> List[SensitiveHit]:
        """
        Multi-scale YuNet detection with landmark-aligned SFace matching.
        The full 15-element detection row (bbox + landmarks + score) is passed
        to IdentityManager.match_face_aligned so it can use cv2.FaceRecognizerSF
        .alignCrop() for geometrically correct face alignment before embedding.
        """
        h_img, w_img = cv_image.shape[:2]
        raw_dets = self._multi_scale_detect(cv_image, w_img, h_img)

        hits = []
        for det in raw_dets:
            x, y, w, h = int(det[0]), int(det[1]), int(det[2]), int(det[3])
            score = float(det[-1])

            x = max(0, x);  y = max(0, y)
            w = min(w_img - x, w);  h = min(h_img - y, h)
            if w <= 0 or h <= 0:
                continue

            identity = None
            if self.identity_manager and match_identities:
                det_row = np.array(det, dtype=np.float32)
                identity = self.identity_manager.match_face_aligned(cv_image, det_row)

            label = f"FACE: {identity}" if identity else "FACE"
            hits.append(SensitiveHit(
                x=x, y=y, w=w, h=h,
                label=label,
                confidence=score,
                identity=identity or "",
            ))

        return hits

    def _detect_bodies(self, cv_image: np.ndarray) -> List[SensitiveHit]:
        """MediaPipe EfficientDet-Lite2 body/person detection."""
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
                cat  = detection.categories[0]
                if cat.category_name in ["person", "face"]:
                    hits.append(SensitiveHit(
                        x=int(bbox.origin_x), y=int(bbox.origin_y),
                        w=int(bbox.width),    h=int(bbox.height),
                        label="BODY",
                        confidence=float(cat.score),
                    ))
        return hits

    def cleanup(self):
        if hasattr(self, "detector") and self.detector:
            try:
                self.detector.close()
            except Exception:
                pass
