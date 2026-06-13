import pytest
from unittest.mock import MagicMock
from src.core.scanner import SafeScanner
from src.core.types import SensitiveHit
from src.core.detectors.vision import VisionDetector
from src.core.detectors.text import RegexDetector


def test_scanner_initialization():
    scanner = SafeScanner()
    assert scanner.face_redaction_mode == "ALL"
    assert scanner.target_identities == []
    assert scanner._vision_cache == {}
    assert scanner._scan_cache == {}


def test_scanner_clear_cache():
    scanner = SafeScanner()
    scanner._vision_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    scanner._scan_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    
    scanner.clear_cache()
    
    assert scanner._vision_cache == {}
    assert scanner._scan_cache == {}


def test_scanner_sets_clear_cache():
    scanner = SafeScanner()
    scanner._vision_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    scanner._scan_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    
    scanner.set_vision_mode("all")
    assert scanner._vision_cache == {}
    assert scanner._scan_cache == {}
    
    scanner._scan_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    scanner.set_face_redaction_mode("BLACKLIST")
    assert scanner._scan_cache == {}
    
    scanner._scan_cache["test_key"] = [SensitiveHit(1, 2, 3, 4, "FACE", 0.9)]
    scanner.set_text_patterns([{"pattern": "test", "label": "TEST"}])
    assert scanner._scan_cache == {}


def test_scanner_scan_caching():
    scanner = SafeScanner()
    
    mock_text_detector = MagicMock(spec=RegexDetector)
    mock_text_detector.detect.return_value = [SensitiveHit(0, 0, 10, 10, "Email", 0.9, "test@example.com")]
    
    mock_vision_detector = MagicMock(spec=VisionDetector)
    mock_vision_detector.detect.return_value = [SensitiveHit(50, 50, 20, 20, "FACE", 0.95)]
    
    scanner.text_detector = mock_text_detector
    scanner.vision_detector = mock_vision_detector
    scanner.detectors = [mock_text_detector, mock_vision_detector]
    
    hits1 = scanner.scan("dummy_path.jpg", cache_key="dummy_path")
    assert len(hits1) == 2
    assert mock_text_detector.detect.call_count == 1
    assert mock_vision_detector.detect.call_count == 1
    
    hits2 = scanner.scan("dummy_path.jpg", cache_key="dummy_path")
    assert len(hits2) == 2
    assert mock_text_detector.detect.call_count == 1
    assert mock_vision_detector.detect.call_count == 1


def test_scanner_face_filtering_modes():
    scanner = SafeScanner()
    
    mock_text_detector = MagicMock(spec=RegexDetector)
    mock_text_detector.detect.return_value = []
    
    mock_vision_detector = MagicMock(spec=VisionDetector)
    mock_vision_detector.detect.return_value = [
        SensitiveHit(10, 10, 20, 20, "FACE", 0.9, identity="Alice"),
        SensitiveHit(50, 50, 20, 20, "FACE", 0.9, identity="Bob"),
        SensitiveHit(100, 100, 20, 20, "FACE", 0.8, identity=None)
    ]
    
    scanner.text_detector = mock_text_detector
    scanner.vision_detector = mock_vision_detector
    scanner.detectors = [mock_text_detector, mock_vision_detector]
    
    # Verify ALL mode redacts all detected faces.
    scanner.set_face_redaction_mode("ALL")
    hits = scanner.scan("dummy.png")
    assert len(hits) == 3
    
    # Verify BLACKLIST mode only redacts matched targets.
    scanner.set_face_redaction_mode("BLACKLIST")
    scanner.target_identities = ["Alice"]
    hits = scanner.scan("dummy.png")
    assert len(hits) == 1
    assert hits[0].identity == "Alice"
    
    # Verify WHITELIST mode protects matched targets and redacts everyone else.
    scanner.set_face_redaction_mode("WHITELIST")
    scanner.target_identities = ["Alice"]
    hits = scanner.scan("dummy.png")
    assert len(hits) == 2
    assert "Alice" not in [h.identity for h in hits]
    assert "Bob" in [h.identity for h in hits]
    assert None in [h.identity for h in hits]
