import os
from typing import List

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class VisionDetector(BaseDetector):
    def __init__(self, mode: str = "faces"):
        self.mode = mode  # "faces", "bodies", or "text"
        
        if self.mode == "faces":
            # Use OpenCV's built-in Haar Cascade for robust frontal face detection
            # This works much better than MediaPipe short-range model for CNICs and group photos.
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        elif self.mode == "bodies":
            model_path = os.path.abspath("efficientdet_lite2.tflite")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Missing body model: {model_path}")
                
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = vision.ObjectDetectorOptions(
                base_options=base_options, score_threshold=0.20, max_results=5
            )
            self.detector = vision.ObjectDetector.create_from_options(options)

    def detect(self, image_path: str) -> List[SensitiveHit]:
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
            
            # Use standard parameters that are good for varying sizes
            # scaleFactor=1.1, minNeighbors=4 is a standard balance between 
            # false positives and missed detections.
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)
            
            for (x, y, w, h) in faces:
                hits.append(
                    SensitiveHit(
                        x=int(x),
                        y=int(y),
                        w=int(w),
                        h=int(h),
                        label="FACE",
                        confidence=0.99, # Haar doesn't return confidence by default easily
                    )
                )

        else:
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
