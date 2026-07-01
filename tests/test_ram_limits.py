import sys
import os
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from unittest.mock import patch, MagicMock

from src.gui.main_window import SafeMARCMainWindow
from src.gui.settings_dialog import SettingsDialog
from src.core.detectors.text import RegexDetector
from src.core.scanner import SafeScanner


class MockDetector:
    def __init__(self):
        self.ocr_cache = {}
        
    def save_cache(self):
        pass


class MockScanner:
    def __init__(self):
        self.text_detector = MockDetector()
        self.cleaned = False
        self.identity_manager = None
        self._scan_cache = {}
        self._vision_cache = {}
        self._regex_cache = {}
        
    def cleanup(self):
        self.cleaned = True
        
    def clear_cache(self):
        pass
        
    def clear_vision_cache(self):
        pass
        
    def set_vision_mode(self, mode):
        pass


class TestRAMLimits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.settings = QSettings("SafeMARC", "SafeMARC")
        self.settings.clear()

    def tearDown(self):
        self.settings.clear()

    def test_settings_dialog_ram_sliders(self):
        scanner = MockScanner()
        dialog = SettingsDialog(scanner)
        
        # Verify RAM limit sliders exist
        self.assertTrue(hasattr(dialog, "slider_soft_ram"))
        self.assertTrue(hasattr(dialog, "slider_hard_ram"))
        
        # Verify soft and hard limits are constrained
        soft_val = dialog.slider_soft_ram.value()
        hard_val = dialog.slider_hard_ram.value()
        self.assertGreaterEqual(hard_val, soft_val + 512)
        
        # Test soft limit change updates settings and hard limit if needed
        dialog.slider_soft_ram.setValue(2048)
        self.assertEqual(int(self.settings.value("soft_ram_limit")), 2048)
        self.assertGreaterEqual(int(self.settings.value("hard_ram_limit")), 2560)
        
        dialog.deleteLater()

    @patch('psutil.Process')
    @patch('src.gui.main_window.SafeScanner')
    def test_reclaim_memory_soft_limit_exceeded(self, mock_safescanner, mock_process_class):
        mock_safescanner.return_value = MockScanner()
        window = SafeMARCMainWindow()
        window.is_batch_mode = True  # Avoid clearing cache due to not being in batch
        
        # Mock current process RSS to return 500 MB
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 500 * 1024 * 1024
        mock_process_class.return_value = mock_proc
        
        # Set limits: Soft 400 MB, Hard 1000 MB -> Should trigger Soft limit
        self.settings.setValue("soft_ram_limit", 400)
        self.settings.setValue("hard_ram_limit", 1000)
        
        # Populate OCR cache with 5 items
        window.scanner.text_detector.ocr_cache = {
            "p1": [("data1", 1.0)],
            "p2": [("data2", 1.0)],
            "p3": [("data3", 1.0)],
            "p4": [("data4", 1.0)],
            "p5": [("data5", 1.0)],
        }
        
        # Trigger reclaim memory
        window.reclaim_memory()
        
        # Should prune OCR cache to exactly 2 elements
        self.assertEqual(len(window.scanner.text_detector.ocr_cache), 2)
        # Should keep the last two: p4 and p5
        self.assertIn("p4", window.scanner.text_detector.ocr_cache)
        self.assertIn("p5", window.scanner.text_detector.ocr_cache)
        self.assertFalse(window.scanner.cleaned)
        window.deleteLater()

    @patch('psutil.Process')
    @patch('src.gui.main_window.SafeScanner')
    def test_reclaim_memory_hard_limit_exceeded(self, mock_safescanner, mock_process_class):
        mock_safescanner.return_value = MockScanner()
        window = SafeMARCMainWindow()
        window.is_batch_mode = True  # Avoid clearing cache due to not being in batch
        
        # Mock current process RSS to return 1200 MB
        mock_proc = MagicMock()
        mock_proc.memory_info.return_value.rss = 1200 * 1024 * 1024
        mock_process_class.return_value = mock_proc
        
        # Set limits: Soft 400 MB, Hard 1000 MB -> Should trigger Hard limit
        self.settings.setValue("soft_ram_limit", 400)
        self.settings.setValue("hard_ram_limit", 1000)
        
        window.scanner.text_detector.ocr_cache = {
            "p1": [("data1", 1.0)],
            "p2": [("data2", 1.0)],
        }
        window.user_selections_cache = {"k1": "val1"}
        
        # Trigger reclaim memory
        window.reclaim_memory()
        
        # Should completely clear OCR cache, user_selections_cache, and clean up scanner detectors
        self.assertEqual(len(window.scanner.text_detector.ocr_cache), 0)
        self.assertEqual(len(window.user_selections_cache), 0)
        self.assertTrue(window.scanner.cleaned)
        window.deleteLater()

    def test_session_only_ocr_cache_preservation(self):
        # Verify RegexDetector doesn't serialize cache to disk
        rd = RegexDetector()
        rd.ocr_cache = {"some_file": [("data", 1.0)]}
        
        # Write mock save/load, they should be no-ops
        rd.save_cache()
        # Verify file is not present
        import os
        from PySide6.QtCore import QStandardPaths
        cache_dir = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
        if cache_dir:
            cache_file = os.path.join(cache_dir, "ocr_cache.json")
            self.assertFalse(os.path.exists(cache_file))


if __name__ == "__main__":
    unittest.main()
