import os
from typing import List

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit
from src.utils.paths import resource_path


class VisionDetector(BaseDetector):
    def __init__(self, mode: str = "faces", identity_manager=None):
        self.mode = mode  # "faces", "bodies", or "text"
        self.identity_manager = identity_manager
        
        if self.mode == "faces":
            # Initialize ensemble of face cascades for maximum coverage of angles, tilts, and side profiles
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.face_cascade_alt = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
            )
            self.profile_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_profileface.xml'
            )
        elif self.mode == "bodies":
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

    def detect(self, image_path: str, match_identities: bool = True) -> List[SensitiveHit]:
        abs_path = os.path.abspath(image_path)
        cv_image = cv2.imread(abs_path)
        if cv_image is None:
            return []

        hits = []

        if self.mode == "text":
            return []

        if self.mode == "faces":
            # Detect faces using a multi-cascade ensemble with rotational searching and contrast equalization
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            h_img, w_img = gray.shape[:2]
            min_face = max(40, min(h_img, w_img) // 30)
            
            # 1. Standard raw grayscale for all core detections (restores perfect default detections and matching accuracy)
            faces_alt = self.face_cascade_alt.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
            )
            # 2. Default Frontal Cascade (Guarantees classic upright frontal face coverage)
            faces_default = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
            )
            # 3. Profile Face Cascade (Detects turned heads and side-profiles. Primarily left-facing)
            faces_profile = self.profile_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
            )
            # 4. Profile Flip: Horizontally flip image to detect right-facing profiles
            flipped_gray = cv2.flip(gray, 1)
            faces_profile_flipped = self.profile_cascade.detectMultiScale(
                flipped_gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
            )
            
            # 5. Supplementary Contrast Pass: Run a robust alternative frontal pass on a separate CLAHE grayscale
            # to capture faces in tricky lighting without distorting the raw gray used by other core cascades.
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
            clahe_gray = clahe.apply(gray)
            faces_alt_clahe = self.face_cascade_alt.detectMultiScale(
                clahe_gray, scaleFactor=1.1, minNeighbors=6, minSize=(min_face, min_face)
            )
            
            raw_boxes = []
            for (x, y, w, h) in faces_alt:
                raw_boxes.append([int(x), int(y), int(w), int(h)])
            for (x, y, w, h) in faces_default:
                raw_boxes.append([int(x), int(y), int(w), int(h)])
            for (x, y, w, h) in faces_profile:
                raw_boxes.append([int(x), int(y), int(w), int(h)])
            for (x, y, w, h) in faces_profile_flipped:
                orig_x = w_img - x - w
                raw_boxes.append([int(orig_x), int(y), int(w), int(h)])
            for (x, y, w, h) in faces_alt_clahe:
                raw_boxes.append([int(x), int(y), int(w), int(h)])
                
            # 6. Rotational Search: For severely tilted posing (e.g. 30+ degree head tilts),
            # rotate the image by -30 and +30 degrees, run the robust alternative frontal cascade,
            # and map coordinates back using inverse affine transformation matrices.
            center = (w_img / 2.0, h_img / 2.0)
            for angle in [-30, 30]:
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated_gray = cv2.warpAffine(gray, M, (w_img, h_img))
                
                faces_rot = self.face_cascade_alt.detectMultiScale(
                    rotated_gray, scaleFactor=1.1, minNeighbors=5, minSize=(min_face, min_face)
                )
                
                for (x, y, w, h) in faces_rot:
                    # Map the center of the rotated box back using inverse matrix
                    cx = x + w / 2.0
                    cy = y + h / 2.0
                    
                    M_inv = cv2.getRotationMatrix2D(center, -angle, 1.0)
                    pts = np.array([[[cx, cy]]], dtype=np.float32)
                    orig_pts = cv2.transform(pts, M_inv)
                    orig_cx, orig_cy = orig_pts[0][0]
                    
                    orig_x = int(orig_cx - w / 2.0)
                    orig_y = int(orig_cy - h / 2.0)
                    raw_boxes.append([orig_x, orig_y, int(w), int(h)])
                
            # --- Union-Based Bounding Box Merging (Union-NMS) ---
            # Partially covered faces or multi-classifier hits produce several overlapping boxes.
            # To ensure the full face region (including hands or hair covering faces) is completely
            # redacted, merge overlapping boxes by taking their coordinate union.
            merged_boxes = []
            for box in raw_boxes:
                bx, by, bw, bh = box
                is_merged = False
                for i, m_box in enumerate(merged_boxes):
                    mx, my, mw, mh = m_box
                    
                    ix = max(bx, mx)
                    iy = max(by, my)
                    iw = min(bx + bw, mx + mw) - ix
                    ih = min(by + bh, my + mh) - iy
                    
                    if iw > 0 and ih > 0:
                        intersect_area = iw * ih
                        box_area = bw * bh
                        m_box_area = mw * mh
                        
                        # Merge boxes if they overlap significantly (> 40% of smaller box area)
                        if intersect_area / min(box_area, m_box_area) > 0.40:
                            min_x = min(bx, mx)
                            min_y = min(by, my)
                            max_x = max(bx + bw, mx + mw)
                            max_y = max(by + bh, my + mh)
                            
                            merged_boxes[i] = [min_x, min_y, max_x - min_x, max_y - min_y]
                            is_merged = True
                            break
                if not is_merged:
                    merged_boxes.append(box)
                    
            for (x, y, w, h) in merged_boxes:
                identity = None
                if self.identity_manager and match_identities:
                    # Clip coordinates to safe image boundaries to prevent cropping out-of-bounds crashes
                    clip_y = max(0, y)
                    clip_h = min(h_img - clip_y, h)
                    clip_x = max(0, x)
                    clip_w = min(w_img - clip_x, w)
                    
                    face_crop = cv_image[clip_y:clip_y+clip_h, clip_x:clip_x+clip_w]
                    if face_crop.size > 0:
                        identity = self.identity_manager.match_face(face_crop)
                        
                label = f"FACE: {identity}" if identity else "FACE"
                
                hits.append(
                    SensitiveHit(
                        x=int(x),
                        y=int(y),
                        w=int(w),
                        h=int(h),
                        label=label,
                        confidence=0.99,
                        identity=identity or ""
                    )
                )
                
                # Keep the UI responsive during long scans
                try:
                    from PySide6.QtWidgets import QApplication
                    if QApplication.instance():
                        QApplication.processEvents()
                except ImportError:
                    pass

        elif self.mode == "bodies":
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
                
            scale = 1
            # Apply linear contrast stretch to improve detection of low-contrast features
            adjusted = cv2.convertScaleAbs(cv_image, alpha=1.5, beta=10)

            rgb_image = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

            result = self.detector.detect(mp_image)

            if result and result.detections:
                for detection in result.detections:
                    bbox = detection.bounding_box
                    cat = detection.categories[0]
                    if cat.category_name in ["person", "face"]:
                        hits.append(
                            SensitiveHit(
                                x=int(bbox.origin_x / scale),
                                y=int(bbox.origin_y / scale),
                                w=int(bbox.width / scale),
                                h=int(bbox.height / scale),
                                label="BODY",
                                confidence=float(cat.score),
                            )
                        )
        return hits

    def cleanup(self):
        if hasattr(self, "detector") and self.detector:
            try:
                self.detector.close()
            except:
                pass
