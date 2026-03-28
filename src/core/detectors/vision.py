import os
from typing import List

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class FaceDetector(BaseDetector):
    def __init__(self):
        model_path = os.path.abspath("efficientdet_lite2.tflite")
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

        orig_h, orig_w, _ = cv_image.shape

        # 1x scale + INTER_AREA
        scale = 1
        scaled = cv2.resize(
            cv_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
        )

        # Linear contrast stretch (Alpha 1.5)
        adjusted = cv2.convertScaleAbs(scaled, alpha=1.5, beta=10)

        rgb_image = cv2.cvtColor(adjusted, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        result = self.detector.detect(mp_image)

        hits = []
        if result and result.detections:
            for detection in result.detections:
                cat = detection.categories[0]

                # Only keep human/face hits
                if cat.category_name in ["person", "face"]:
                    bbox = detection.bounding_box

                    # Map coordinates back to original image size
                    hits.append(
                        SensitiveHit(
                            x=int(bbox.origin_x / scale),
                            y=int(bbox.origin_y / scale),
                            w=int(bbox.width / scale),
                            h=int(bbox.height / scale),
                            label="FACE",
                            confidence=float(cat.score),
                        )
                    )
        return hits
