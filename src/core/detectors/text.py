import re
from typing import List

import pytesseract
from PIL import Image

from src.core.detectors.base import BaseDetector
from src.core.types import SensitiveHit


class RegexDetector(BaseDetector):
    def __init__(self):
        # Define patterns here
        self.patterns = {
            "PHONE_PK": re.compile(r"\b03\d{2}[-]?\d{7}\b"),  # 0300-1234567
            "CNIC": re.compile(r"\b\d{5}[-]?\d{7}[-]?\d{1}\b"),  # 42101...
            "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        }

    def detect(self, image_path: str) -> List[SensitiveHit]:
        img = Image.open(image_path)
        # Get verbose data: left, top, width, height, text
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        hits = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            if not text:
                continue

            # Check all patterns
            for label, pattern in self.patterns.items():
                if pattern.search(text):
                    hits.append(
                        SensitiveHit(
                            x=data["left"][i],
                            y=data["top"][i],
                            w=data["width"][i],
                            h=data["height"][i],
                            label=label,
                            confidence=float(data["conf"][i]),
                            text_content=text,
                        )
                    )
                    break  # Don't double-count
        return hits
