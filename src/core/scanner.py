from typing import List, Dict, Optional
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
        self.face_redaction_mode: str = "ALL"  # "ALL", "BLACKLIST", "WHITELIST"
        self.target_identities: List[str] = [] # Names to filter on.
        
        self._vision_cache: Dict[str, List[SensitiveHit]] = {}  # Map of file path to SensitiveHit list.
        self._regex_cache: Dict[str, List[SensitiveHit]] = {}   # Map of file path to SensitiveHit list.
        self._scan_cache: Dict[str, List[SensitiveHit]] = {}    # Map of cache key to SensitiveHit list.
        
    def clear_cache(self) -> None:
        self._vision_cache = {}
        self._regex_cache = {}
        self._scan_cache = {}
        print("[SafeScanner] Session scan caches cleared.")
        
    def clear_scan_cache_only(self) -> None:
        self._scan_cache = {}
        print("[SafeScanner] Filter scan cache cleared.")
        
    def clear_text_cache(self) -> None:
        self._regex_cache = {}
        self._scan_cache = {}
        print("[SafeScanner] Text/Regex cache cleared.")
        
    def clear_vision_cache(self) -> None:
        self._vision_cache = {}
        self._scan_cache = {}
        print("[SafeScanner] Vision caches cleared.")
        
    def set_vision_mode(self, mode: str) -> None:
        if hasattr(self, "vision_detector") and self.vision_detector:
            try:
                self.vision_detector.cleanup()
            except Exception:
                pass
        self.vision_detector = VisionDetector(mode=mode, identity_manager=self.identity_manager)
        self.detectors = [self.text_detector, self.vision_detector]
        self.clear_cache()
 
    def set_face_redaction_mode(self, mode: str) -> None:
        self.face_redaction_mode = mode
        self.clear_scan_cache_only()
 
    def set_text_patterns(self, patterns_list: List[dict]) -> None:
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
        self.clear_text_cache()
 
    def scan(self, file_path: str, pdf_words: Optional[list] = None, cache_key: Optional[str] = None) -> List[SensitiveHit]:
        """Runs all detectors and returns combined hits."""
        ckey = cache_key if cache_key else file_path
        if ckey in self._scan_cache:
            print(f"  [CACHE] Reusing {len(self._scan_cache[ckey])} cached scan hits for {ckey}.")
            return list(self._scan_cache[ckey])
 
        all_hits = []
        print(f"Scanning: {file_path}")
 
        if ckey in self._regex_cache:
            print(f"  [CACHE] Reusing {len(self._regex_cache[ckey])} cached regex hits for {ckey}.")
            regex_hits = self._regex_cache[ckey]
        else:
            try:
                regex_hits = self.text_detector.detect(file_path, pdf_words=pdf_words)
            except Exception as e:
                print(f"RegexDetector failed: {e}")
                regex_hits = []
            self._regex_cache[ckey] = list(regex_hits)
 
        if ckey in self._vision_cache:
            print(f"  [CACHE] Reusing {len(self._vision_cache[ckey])} cached vision hits for {ckey}.")
            vision_hits = self._vision_cache[ckey]
        else:
            try:
                vision_hits = self.vision_detector.detect(file_path, match_identities=True)
            except Exception as e:
                print(f"VisionDetector failed: {e}")
                vision_hits = []
            self._vision_cache[ckey] = list(vision_hits)
 
        all_hits.extend(regex_hits)
        all_hits.extend(vision_hits)
 
        final_hits = []
        for hit in all_hits:
            if hit.label.startswith("FACE") or hit.label == "BODY":
                if self.face_redaction_mode == "ALL":
                    final_hits.append(hit)
                elif self.face_redaction_mode == "BLACKLIST":
                    if hit.identity and hit.identity in self.target_identities:
                        final_hits.append(hit)
                        print(f"  [BLACKLIST] KEEP '{hit.identity}' (in target list)")
                    else:
                        print(f"  [BLACKLIST] SKIP identity='{hit.identity}' targets={self.target_identities}")
                elif self.face_redaction_mode == "WHITELIST":
                    if hit.identity and hit.identity in self.target_identities:
                        print(f"  [WHITELIST] PROTECT '{hit.identity}' (whitelisted)")
                    else:
                        final_hits.append(hit)
                        print(f"  [WHITELIST] REDACT identity='{hit.identity}'")
            else:
                final_hits.append(hit)

        print(f"[SafeScanner] Filtered {len(all_hits)} down to {len(final_hits)} hits ({self.face_redaction_mode} mode)")
        self._scan_cache[ckey] = list(final_hits)
        return final_hits

    def cleanup(self) -> None:
        for detector in self.detectors:
            if hasattr(detector, "cleanup"):
                detector.cleanup()

    def redact(self, file_path: str, output_path: str, hits: List[SensitiveHit]) -> bool:
        """Applies redaction based on hits."""
        return self.redactor.apply(file_path, output_path, hits)
