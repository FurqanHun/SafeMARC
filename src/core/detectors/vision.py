import os
from typing import List

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class VisionDetector(BaseDetector):
    def __init__(self, mode: str = "faces", identity_manager=None):
        self.mode = mode  # "faces", "bodies", or "text"
        self.identity_manager = identity_manager
        
        if self.mode == "faces":
            # Use OpenCV's built-in Haar Cascade for robust frontal face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        elif self.mode == "bodies":
            model_path = os.path.abspath("assets/efficientdet_lite2.tflite")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Missing body model: {model_path}")
                
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=0.20, max_results=5
            )
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
            # Detect faces using Haar Cascade
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # minNeighbors=8 reduces false positives (clothing/textures)
            # minSize=(40,40) ignores tiny detections that are unlikely to be faces
            h_img, w_img = gray.shape[:2]
            min_face = max(40, min(h_img, w_img) // 30)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=8, minSize=(min_face, min_face)
            )
            
            for (x, y, w, h) in faces:
                identity = None
                if self.identity_manager and match_identities:
                    # Crop face for recognition
                    face_crop = cv_image[y:y+h, x:x+w]
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
            # Detect bodies using MediaPipe EfficientDet
            scale = 1
            # Linear contrast stretch helps with some detections
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
