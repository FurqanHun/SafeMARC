from typing import List

from src.core.detectors.text import RegexDetector
from src.core.detectors.vision import VisionDetector
from src.core.redactor import Redactor  # You implement this next
from src.core.types import SensitiveHit


class SafeScanner:
    def __init__(self, vision_mode: str = "faces"):
        self.vision_detector = VisionDetector(mode=vision_mode)
        self.text_detector = RegexDetector()
        self.detectors = [self.text_detector, self.vision_detector]
        self.redactor = Redactor()
        
    def set_vision_mode(self, mode: str):
        # Re-initialize the vision detector with the new mode
        self.vision_detector = VisionDetector(mode=mode)
        self.detectors = [self.text_detector, self.vision_detector]

    def set_text_patterns(self, patterns_list):
        """
        patterns_list should be a list of dicts: 
        [{"label": "...", "pattern": "...", "is_regex": bool}]
        """
        self.text_detector.clear_custom_patterns()
        for p in patterns_list:
            if p["pattern"].strip():
                self.text_detector.add_custom_pattern(
                    label=p.get("label", "TEXT"),
                    pattern=p["pattern"],
                    is_regex=p.get("is_regex", False),
                    is_whole_word=p.get("whole_word", False)
                )

    def scan(self, file_path: str) -> List[SensitiveHit]:
        """Runs all detectors and returns combined hits."""
        all_hits = []
        print(f"Scanning: {file_path}")

        for detector in self.detectors:
            try:
                hits = detector.detect(file_path)
                all_hits.extend(hits)
            except Exception as e:
                print(f"Detector failed: {e}")

        return all_hits

    def redact(self, file_path: str, output_path: str, hits: List[SensitiveHit]):
        """Applies redaction based on hits."""
        return self.redactor.apply(file_path, output_path, hits)
