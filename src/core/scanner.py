from typing import List
from src.core.detectors.text import RegexDetector
from src.core.detectors.vision import VisionDetector
from src.core.redactor import Redactor
from src.core.types import SensitiveHit
from src.core.identity_manager import IdentityManager

class SafeScanner:
    def __init__(self, vision_mode: str = "faces"):
        self.identity_manager = IdentityManager()
        self.vision_detector = VisionDetector(mode=vision_mode, identity_manager=self.identity_manager)
        self.text_detector = RegexDetector()
        self.detectors = [self.text_detector, self.vision_detector]
        self.redactor = Redactor()
        self.face_redaction_mode = "ALL"  # "ALL", "BLACKLIST", "WHITELIST"
        self.target_identities = [] # List of names to filter on
        
        # Performance session vision cache
        self._vision_cache = {}  # file_path -> list of SensitiveHit
        
    def clear_cache(self):
        self._vision_cache = {}
        print("[SafeScanner] Vision session cache cleared.")
        
    def set_vision_mode(self, mode: str):
        # Re-initialize the vision detector with the new mode
        self.vision_detector = VisionDetector(mode=mode, identity_manager=self.identity_manager)
        self.detectors = [self.text_detector, self.vision_detector]
        self.clear_cache()

    def set_face_redaction_mode(self, mode: str):
        self.face_redaction_mode = mode

    def set_text_patterns(self, patterns_list):
        self.text_detector.clear_custom_patterns()
        for p in patterns_list:
            if p["pattern"].strip():
                self.text_detector.add_custom_pattern(
                    label=p.get("label", "TEXT"),
                    pattern=p["pattern"],
                    is_regex=p.get("is_regex", False),
                    is_whole_word=p.get("whole_word", False),
                    keywords=p.get("keywords")
                )

    def scan(self, file_path: str, pdf_words: list = None, cache_key: str = None) -> List[SensitiveHit]:
        """Runs all detectors and returns combined hits."""
        all_hits = []
        print(f"Scanning: {file_path}")

        # Check if we have cached vision hits for this file in the session cache
        ckey = cache_key if cache_key else file_path
        use_cached_vision = (ckey in self._vision_cache)

        for detector in self.detectors:
            try:
                if isinstance(detector, RegexDetector):
                    hits = detector.detect(file_path, pdf_words=pdf_words)
                elif isinstance(detector, VisionDetector):
                    if use_cached_vision:
                        print(f"  [CACHE] Reusing {len(self._vision_cache[ckey])} cached vision hits for {ckey}.")
                        hits = self._vision_cache[ckey]
                    else:
                        # Always detect and match identities on first run so we have all names cached
                        hits = detector.detect(file_path, match_identities=True)
                        self._vision_cache[ckey] = list(hits)
                else:
                    hits = detector.detect(file_path)
                all_hits.extend(hits)
            except Exception as e:
                print(f"Detector failed: {e}")

        # Filter Face Hits based on mode
        final_hits = []
        for hit in all_hits:
            if hit.label.startswith("FACE") or hit.label == "BODY":
                if self.face_redaction_mode == "ALL":
                    final_hits.append(hit)
                elif self.face_redaction_mode == "BLACKLIST":
                    # Only redact faces whose identity is in our target list.
                    # Unrecognized faces (empty identity) are NOT redacted.
                    # If target list is empty, nobody gets redacted.
                    if hit.identity and hit.identity in self.target_identities:
                        final_hits.append(hit)
                        print(f"  [BLACKLIST] KEEP '{hit.identity}' (in target list)")
                    else:
                        print(f"  [BLACKLIST] SKIP identity='{hit.identity}' targets={self.target_identities}")
                elif self.face_redaction_mode == "WHITELIST":
                    # Redact everyone EXCEPT faces whose identity is in target list.
                    # Unrecognized faces always get redacted.
                    # If target list is empty, everyone gets redacted.
                    if hit.identity and hit.identity in self.target_identities:
                        print(f"  [WHITELIST] PROTECT '{hit.identity}' (whitelisted)")
                    else:
                        final_hits.append(hit)
                        print(f"  [WHITELIST] REDACT identity='{hit.identity}'")
            else:
                # Keep text hits as is
                final_hits.append(hit)

        print(f"[SafeScanner] Filtered {len(all_hits)} down to {len(final_hits)} hits ({self.face_redaction_mode} mode)")
        return final_hits

    def cleanup(self):
        for detector in self.detectors:
            if hasattr(detector, "cleanup"):
                detector.cleanup()

    def redact(self, file_path: str, output_path: str, hits: List[SensitiveHit]):
        """Applies redaction based on hits."""
        return self.redactor.apply(file_path, output_path, hits)
