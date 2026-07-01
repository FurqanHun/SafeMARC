import logging
logger = logging.getLogger(__name__)
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


_YUNET_SCORE_THRESH = 0.70
_YUNET_NMS_THRESH   = 0.30
_YUNET_TOP_K        = 5000
_LARGE_FACE_MAX_DIM = 640


def _load_yunet(model_path: str, input_size: tuple, score_threshold: float = _YUNET_SCORE_THRESH) -> cv2.FaceDetectorYN:
    """Instantiate a YuNet FaceDetectorYN for the given input resolution."""
    return cv2.FaceDetectorYN.create(
        model=model_path,
        config="",
        input_size=input_size,
        score_threshold=score_threshold,
        nms_threshold=_YUNET_NMS_THRESH,
        top_k=_YUNET_TOP_K,
    )


def _is_matching_face_body(fx: int, fy: int, fw: int, fh: int, bx: int, by: int, bw: int, bh: int) -> bool:
    """Checks if a face spatially matches the upper section of a body bounding box."""
    # 1. Face center must be inside body box horizontally (with a 10% body width margin)
    face_cx = fx + fw / 2
    if not (bx - bw * 0.1 <= face_cx <= bx + bw * 1.1):
        return False
    # 2. Face center must be above the middle of the body box,
    # and not more than 2.0x face height above the top of the body box.
    face_cy = fy + fh / 2
    if not (by - fh * 2.0 <= face_cy <= by + bh * 0.5):
        return False
    # 3. Size ratio check: body shouldn't be disproportionately huge (e.g. > 50x face area)
    face_area = fw * fh
    body_area = bw * bh
    if body_area / max(face_area, 1) > 50.0:
        return False
    return True


class VisionDetector(BaseDetector):
    """Encapsulates facial and full-body detection models, including multi-scale tracking and memory reclamation."""

    def __init__(self, mode: str = "faces", identity_manager=None):
        self.mode = mode
        self.identity_manager = identity_manager
        self._local = threading.local()

        self._yunet_model_path = resource_path("assets/face_detection_yunet_2023mar.onnx")

        if self.mode == "bodies":
            model_path = resource_path("assets/efficientdet_lite2.tflite")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Missing body model: {model_path}")

            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            bd_val = float(settings.value("model_body_detect", 0.25))

            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=bd_val, max_results=100
            )
            logger.debug(f"[DEBUG] Initializing ObjectDetector with dynamic threshold: {bd_val:.2f}")
            self.detector = vision.ObjectDetector.create_from_options(options)

        elif self.mode == "faces":
            if not os.path.exists(self._yunet_model_path):
                raise FileNotFoundError(
                    f"Missing YuNet model: {self._yunet_model_path}\n"
                    "Download with:\n"
                    "  curl -L -o assets/face_detection_yunet_2023mar.onnx "
                    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/"
                    "face_detection_yunet_2023mar.onnx"
                )

    def _get_yunet(self, w: int, h: int, thresh: float) -> cv2.FaceDetectorYN:
        """Native-resolution thread-local YuNet, re-created when size or threshold changes."""
        if (getattr(self._local, "yunet", None) is None
                or getattr(self._local, "yunet_size", None) != (w, h)
                or getattr(self._local, "yunet_thresh", None) != thresh):
            self._local.yunet = _load_yunet(self._yunet_model_path, (w, h), thresh)
            self._local.yunet_size = (w, h)
            self._local.yunet_thresh = thresh
        return self._local.yunet

    def _get_yunet_small(self, w: int, h: int, thresh: float) -> cv2.FaceDetectorYN:
        """Downscaled-pass thread-local YuNet instance."""
        if (getattr(self._local, "yunet_small", None) is None
                or getattr(self._local, "yunet_small_size", None) != (w, h)
                or getattr(self._local, "yunet_thresh_small", None) != thresh):
            self._local.yunet_small = _load_yunet(self._yunet_model_path, (w, h), thresh)
            self._local.yunet_small_size = (w, h)
            self._local.yunet_thresh_small = thresh
        return self._local.yunet_small

    def _multi_scale_detect(self, cv_image: np.ndarray, w_img: int, h_img: int, face_thresh: float) -> list:
        """
        Run YuNet at native resolution, then at a downscaled resolution when
        the image is large (catches portrait-sized faces > 300px which YuNet's
        training range doesn't cover at native scale).  Results are merged with
        containment-aware NMS.
        """
        all_dets = []

        yunet = self._get_yunet(w_img, h_img, face_thresh)
        _, dets = yunet.detect(cv_image)
        if dets is not None:
            all_dets.extend(dets.tolist())

        if max(w_img, h_img) > _LARGE_FACE_MAX_DIM:
            scale = _LARGE_FACE_MAX_DIM / max(w_img, h_img)
            sw = max(1, int(w_img * scale))
            sh = max(1, int(h_img * scale))
            small = cv2.resize(cv_image, (sw, sh), interpolation=cv2.INTER_AREA)

            yunet_s = self._get_yunet_small(sw, sh, face_thresh)
            _, dets_s = yunet_s.detect(small)
            if dets_s is not None:
                for d in dets_s.tolist():
                    d_up = list(d)
                    for i in range(14):
                        d_up[i] = d_up[i] / scale
                    all_dets.append(d_up)

        return self._nms(all_dets)

    def _nms(self, detections: list, iou_thresh: float = 0.40, use_iou: bool = False) -> list:
        """
        Greedy NMS sorted by confidence.

        When use_iou is False (default, used for faces), suppression uses
        containment ratio (intersection / smaller area) so sub-face
        detections (lips, eyes) inside a larger face box are removed.

        When use_iou is True (used for bodies), suppression uses standard
        IoU (intersection / union) which preserves overlapping but distinct
        people standing close together in group photos.
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
                    if use_iou:
                        # Standard IoU: intersection / union
                        union = bw * bh + kw * kh - inter
                        if inter / max(union, 1) > iou_thresh:
                            suppressed = True
                            break
                    else:
                        # Containment ratio: intersection / smaller area
                        min_area = min(bw * bh, kw * kh)
                        if inter / max(min_area, 1) > iou_thresh:
                            suppressed = True
                            break
            if not suppressed:
                kept.append(det)

        return kept



    def detect(self, image_path: str, match_identities: bool = True) -> List[SensitiveHit]:
        abs_path = os.path.abspath(image_path)
        cv_image = cv2.imread(abs_path)
        if cv_image is None:
            return []

        if self.mode == "text":
            return []
        if self.mode == "faces":
            res = self._detect_faces(cv_image, match_identities)
            self._reclaim_if_needed()
            return res
        if self.mode == "bodies":
            res = self._detect_bodies(cv_image, match_identities)
            self._reclaim_if_needed()
            return res
        return []

    def _detect_faces(self, cv_image: np.ndarray, match_identities: bool, face_thresh: Optional[float] = None) -> List[SensitiveHit]:
        """
        Multi-scale YuNet detection with landmark-aligned SFace matching.
        The full 15-element detection row (bbox + landmarks + score) is passed
        to IdentityManager.match_face_aligned so it can use cv2.FaceRecognizerSF
        .alignCrop() for geometrically correct face alignment before embedding.
        """
        if face_thresh is None:
            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            face_thresh = float(settings.value("model_face_detect_yunet", _YUNET_SCORE_THRESH))

        h_img, w_img = cv_image.shape[:2]
        raw_dets = self._multi_scale_detect(cv_image, w_img, h_img, face_thresh)
        num_faces = len(raw_dets)

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
                identity = self.identity_manager.match_face_aligned(
                    cv_image, det_row, num_faces=num_faces
                )

            label = f"FACE: {identity}" if identity else "FACE"
            hits.append(SensitiveHit(
                x=x, y=y, w=w, h=h,
                label=label,
                confidence=score,
                identity=identity or "",
            ))

        return hits

    def _detect_bodies(self, cv_image: np.ndarray, match_identities: bool = True) -> List[SensitiveHit]:
        """MediaPipe EfficientDet-Lite2 body/person detection with identity matching."""
        from PySide6.QtCore import QSettings
        settings = QSettings("SafeMARC", "SafeMARC")
        bd_val = float(settings.value("model_body_detect", 0.25))

        if not hasattr(self, "_active_bd_val") or self._active_bd_val != bd_val or not getattr(self, "detector", None):
            logger.debug(f"[DEBUG] Recreating ObjectDetector with active threshold: {bd_val:.2f}")
            if hasattr(self, "detector") and self.detector:
                try:
                    self.detector.close()
                except Exception:
                    pass
            self._active_bd_val = bd_val
            model_path = resource_path("assets/efficientdet_lite2.tflite")
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=bd_val, max_results=100
            )
            self.detector = vision.ObjectDetector.create_from_options(options)

        # Run face detection with identity matching first, so we can map face identities to bodies.
        faces = []
        try:
            faces = self._detect_faces(cv_image, match_identities=match_identities, face_thresh=_YUNET_SCORE_THRESH)
        except Exception as e:
            logger.error(f"[DEBUG] Face detection in body scan failed: {e}")

        # Adaptive CLAHE contrast enhancement for low-light images
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        mean_brightness = cv2.mean(gray)[0]
        if mean_brightness < 90:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            cl = clahe.apply(l)
            limg = cv2.merge((cl, a, b))
            adjusted = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        else:
            adjusted = cv_image

        h, w = adjusted.shape[:2]

        # Upscale small images (max dim < 640) by 2× so EfficientDet can resolve small bodies.
        upscale_factor = 1
        if max(w, h) < 640:
            upscale_factor = 2
            adjusted = cv2.resize(adjusted, (w * 2, h * 2), interpolation=cv2.INTER_LINEAR)
            h, w = adjusted.shape[:2]

        full_dets = []

        # Pass 1: Full image
        rgb_image = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
        result = self.detector.detect(mp_image)
        if result and result.detections:
            for d in result.detections:
                cat = d.categories[0]
                if cat.category_name == "person":
                    bbox = d.bounding_box
                    full_dets.append((
                        int(bbox.origin_x), int(bbox.origin_y),
                        int(bbox.width), int(bbox.height),
                        float(cat.score)
                    ))

        all_detections = list(full_dets)
        
        del rgb_image
        del mp_image
        del result
        self._reclaim_if_needed()

        # Pass 2: Adaptive tiling — grid density scales with image size
        max_dim = max(w, h)
        if max_dim >= 5000:
            cols, rows = 4, 3
        elif max_dim >= 3500:
            cols, rows = 3, 3
        elif max_dim >= 2000:
            cols, rows = 2, 2
        else:
            cols, rows = 0, 0  # No tiling for small images

        if cols > 0 and rows > 0:
            overlap = 100
            tile_w = w // cols
            tile_h = h // rows
            tiles = []
            for r in range(rows):
                for c in range(cols):
                    tx1 = max(0, c * tile_w - overlap)
                    ty1 = max(0, r * tile_h - overlap)
                    tx2 = min(w, (c + 1) * tile_w + overlap)
                    ty2 = min(h, (r + 1) * tile_h + overlap)
                    tiles.append((tx1, ty1, tx2, ty2))

            for tx1, ty1, tx2, ty2 in tiles:
                tile_img = adjusted[ty1:ty2, tx1:tx2]
                if tile_img.size == 0:
                    continue
                tile_rgb = cv2.cvtColor(tile_img, cv2.COLOR_BGR2RGB)
                tile_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=tile_rgb)
                tile_result = self.detector.detect(tile_mp)
                if tile_result and tile_result.detections:
                    for d in tile_result.detections:
                        cat = d.categories[0]
                        if cat.category_name == "person":
                            bbox = d.bounding_box
                            abs_x = tx1 + bbox.origin_x
                            abs_y = ty1 + bbox.origin_y
                            tw, th = int(bbox.width), int(bbox.height)

                            # Discard tile detection if it is highly contained inside an existing detection
                            is_duplicate = False
                            for fx, fy, fw, fh, fscore in all_detections:
                                ix = max(abs_x, fx)
                                iy = max(abs_y, fy)
                                iw = min(abs_x + tw, fx + fw) - ix
                                ih = min(abs_y + th, fy + fh) - iy
                                if iw > 0 and ih > 0:
                                    inter = iw * ih
                                    if inter / max(tw * th, 1) > 0.50:
                                        is_duplicate = True
                                        break

                            if not is_duplicate:
                                all_detections.append((
                                    int(abs_x), int(abs_y),
                                    tw, th,
                                    float(cat.score)
                                ))
                del tile_img
                del tile_rgb
                del tile_mp
                del tile_result
                self._reclaim_if_needed()

        # Scale coordinates back to original resolution if upscaled
        if upscale_factor > 1:
            all_detections = [
                (int(x / upscale_factor), int(y / upscale_factor),
                 int(bw / upscale_factor), int(bh / upscale_factor), score)
                for x, y, bw, bh, score in all_detections
            ]
            h, w = h // upscale_factor, w // upscale_factor

        # Run NMS on all detections (standard IoU for bodies to preserve distinct people)
        suppressed = []
        if all_detections:
            suppressed = self._nms(all_detections, iou_thresh=0.55, use_iou=True)

        hits = []
        for x, y, w_box, h_box, score in suppressed:
            # Bounds safety
            x = max(0, x)
            y = max(0, y)
            w_box = min(w - x, w_box)
            h_box = min(h - y, h_box)
            if w_box <= 0 or h_box <= 0:
                continue

            # Reject slivers that are clearly not a person (hands, arms, necks).
            # A standing/sitting person's height should be at least half their width.
            if h_box < w_box * 0.5:
                continue

            # Associate face identity with this body box if they match
            body_identity = ""
            for face in faces:
                if _is_matching_face_body(face.x, face.y, face.w, face.h, x, y, w_box, h_box):
                    body_identity = face.identity
                    break

            hits.append(SensitiveHit(
                x=x, y=y, w=w_box, h=h_box,
                label="BODY",
                confidence=score,
                identity=body_identity
            ))

        # Face-guided estimation & recovery for any uncovered faces
        for face in faces:
            fx, fy, fw, fh = face.x, face.y, face.w, face.h
            
            # Check if this face is covered by any final body hit
            covered = False
            for hit in hits:
                if _is_matching_face_body(fx, fy, fw, fh, hit.x, hit.y, hit.w, hit.h):
                    covered = True
                    break
            
            if not covered:
                # Generate estimated body box centering the face (with tighter constraints)
                ew = int(fw * 2.5)
                eh = int(fh * 4.5)
                ex = int(fx - (ew - fw) / 2)
                ey = int(fy)
                
                ex = max(0, ex)
                ey = max(0, ey)
                ew = min(w - ex, ew)
                eh = min(h - ey, eh)
                
                if ew > 0 and eh > 0:
                    hits.append(SensitiveHit(
                        x=ex, y=ey, w=ew, h=eh,
                        label="BODY",
                        confidence=face.confidence,
                        identity=face.identity
                    ))
        hits = self._depth_clip_bodies(hits)

        hits = [h for h in hits if h.h >= h.w * 0.5]

        return hits

    def _depth_clip_bodies(self, hits: List[SensitiveHit]) -> List[SensitiveHit]:
        """Clip overlapping body boxes so back-row boxes don't cover front-row faces.

        Depth heuristic: a box whose bottom edge (y + h) is further down the
        image is considered "in front" (closer to the camera in a typical
        group photo).  When a "behind" box's bottom extends past the top of
        an "in front" box, the behind box is trimmed.
        """
        if len(hits) < 2:
            return hits

        result = []
        for i, behind in enumerate(hits):
            bx, by, bw, bh = behind.x, behind.y, behind.w, behind.h
            b_bottom = by + bh

            for j, front in enumerate(hits):
                if i == j:
                    continue

                fx, fy, fw, fh = front.x, front.y, front.w, front.h
                f_bottom = fy + fh

                # Front box must be genuinely "in front" (bottom edge lower)
                if f_bottom <= b_bottom:
                    continue

                # Check horizontal overlap (need significant overlap, not just touching)
                ox1 = max(bx, fx)
                ox2 = min(bx + bw, fx + fw)
                h_overlap = ox2 - ox1
                if h_overlap < min(bw, fw) * 0.3:
                    continue

                # If behind box's bottom extends past front box's top, clip it
                if b_bottom > fy:
                    new_h = fy - by
                    # Only clip if we keep at least 30% of the original height
                    if new_h >= bh * 0.30:
                        bh = new_h
                        b_bottom = by + bh

            if bh > 0:
                result.append(SensitiveHit(
                    x=bx, y=by, w=bw, h=bh,
                    label=behind.label,
                    confidence=behind.confidence,
                    text_content=behind.text_content,
                    identity=behind.identity
                ))
        return result

    def cleanup(self):
        if hasattr(self, "detector") and self.detector:
            try:
                self.detector.close()
            except Exception:
                pass
            self.detector = None
        if hasattr(self, "_active_bd_val"):
            delattr(self, "_active_bd_val")

    def _reclaim_if_needed(self):
        try:
            import os
            import psutil
            process = psutil.Process(os.getpid())
            current_rss = process.memory_info().rss / (1024 * 1024)
        except Exception:
            current_rss = 0
        
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("SafeMARC", "SafeMARC")
            soft_limit = int(settings.value("soft_ram_limit", 1500))
        except Exception:
            soft_limit = 1500
        
        if current_rss > soft_limit:
            import gc
            gc.collect()
            import sys
            if sys.platform.startswith("linux"):
                try:
                    import ctypes
                    libc = ctypes.CDLL("libc.so.6")
                    libc.malloc_trim(0)
                except Exception:
                    pass
            elif sys.platform.startswith("win32"):
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.SetProcessWorkingSetSize(kernel32.GetCurrentProcess(), -1, -1)
                except Exception:
                    pass
