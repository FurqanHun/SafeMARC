import sys
import os
import unittest
from PySide6.QtWidgets import QApplication, QListWidgetItem
from PySide6.QtCore import Qt

from src.gui.main_window import SafeMARCMainWindow
from src.core.types import SensitiveHit

class TestPDFNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_pdf_navigation_lifecycle(self):
        class MockScanner:
            _scan_cache = {}
            def clear_cache(self):
                pass
            def redact(self, path, out, hits):
                return True
            def scan(self, path, pdf_words=None):
                return []

        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        window.is_batch_mode = True
        window.batch_index = 0
        
        # Add item to file list
        item = QListWidgetItem("test.pdf")
        item.setData(Qt.UserRole, "test.pdf")
        window.file_list.addItem(item)
        
        # Setup active PDF page data simulating a 3-page PDF
        window.active_pdf_source = "test.pdf"
        window.active_pdf_pages = [
            {"image_path": "page0.png", "words": []},
            {"image_path": "page1.png", "words": []},
            {"image_path": "page2.png", "words": []}
        ]
        window.active_pdf_outputs = ["page0.png", "page1.png", "page2.png"]
        window.active_pdf_index = 0
        
        # Load next item to trigger PDF loop processing
        window.load_next_batch_item()
        
        # 1. Verify container is visible and showing correct values
        self.assertFalse(window.pdf_nav_container.isHidden())
        self.assertEqual(window.pdf_page_spin.value(), 1)
        self.assertEqual(window.pdf_page_spin.maximum(), 3)
        self.assertEqual(window.pdf_total_label.text(), "/ 3")
        
        # 2. Simulate user drawing/selecting hits on Page 1 (index 0)
        hit = SensitiveHit(5, 5, 10, 10, "MANUAL", 1.0)
        window.preview_widget.active_hits = [hit]
        
        # 3. Simulate jumping directly to Page 3 (index 2) via the SpinBox
        window.pdf_page_spin.setValue(3)
        
        # Verify page index updated and previous page's selections cached
        self.assertEqual(window.active_pdf_index, 2)
        cache_key_0 = "test.pdf_page_0"
        self.assertIn(cache_key_0, window.user_selections_cache)
        self.assertTrue(window.user_selections_cache[cache_key_0]["reviewed"])
        self.assertEqual(window.user_selections_cache[cache_key_0]["active_hits"], [hit])
        
        # Since we jumped directly to Page 3, Page 2 (index 1) was skipped entirely (reviewed=False or not in cache)
        cache_key_1 = "test.pdf_page_1"
        self.assertNotIn(cache_key_1, window.user_selections_cache)
        
        # Add a hit to Page 3 (index 2)
        hit3 = SensitiveHit(20, 20, 30, 30, "FACE", 0.9)
        window.preview_widget.active_hits = [hit3]
        
        # 4. Finalize PDF redaction
        window._finalize_pdf_redaction()
        
        # Verify Page 1 (index 0) got redacted (has a temp file output path)
        self.assertNotEqual(window.active_pdf_outputs[0], "page0.png")
        self.assertTrue(window.active_pdf_outputs[0].endswith(".png"))
        
        # Verify Page 2 (index 1) stayed the original page path (auto-skipped since unvisited)
        self.assertEqual(window.active_pdf_outputs[1], "page1.png")
        
        # Verify Page 3 (index 2) got redacted (has a temp file output path)
        self.assertNotEqual(window.active_pdf_outputs[2], "page2.png")
        self.assertTrue(window.active_pdf_outputs[2].endswith(".png"))
        
        # Clean up temp files created during finalize
        for out in window.active_pdf_outputs:
            if out.startswith("/tmp") or "safemarc_temp" in out:
                if os.path.exists(out):
                    os.remove(out)

    def test_skip_remaining_pages(self):
        class MockScanner:
            _scan_cache = {}
            def clear_cache(self):
                pass
            def redact(self, path, out, hits):
                return True
            def scan(self, path, pdf_words=None):
                return []

        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        window.is_batch_mode = True
        window.batch_index = 0
        
        # Add item to file list
        item = QListWidgetItem("test.pdf")
        item.setData(Qt.UserRole, "test.pdf")
        window.file_list.addItem(item)
        
        # Setup active PDF page data simulating a 3-page PDF
        window.active_pdf_source = "test.pdf"
        window.active_pdf_pages = [
            {"image_path": "page0.png", "words": []},
            {"image_path": "page1.png", "words": []},
            {"image_path": "page2.png", "words": []}
        ]
        window.active_pdf_outputs = ["page0.png", "page1.png", "page2.png"]
        window.active_pdf_index = 0
        
        # Load next item to trigger PDF loop processing
        window.load_next_batch_item()
        
        # Mock PDFHandler.build_pdf to capture the compiled outputs
        from src.utils.pdf_handler import PDFHandler
        built_outputs = []
        original_build_pdf = PDFHandler.build_pdf
        try:
            def mock_build_pdf(outputs, output_path):
                nonlocal built_outputs
                built_outputs = list(outputs)
                return True
            PDFHandler.build_pdf = mock_build_pdf
            
            # User reviews Page 1 (index 0) and adds a manual hit
            hit = SensitiveHit(10, 10, 15, 15, "MANUAL", 1.0)
            window.preview_widget.active_hits = [hit]
            
            # Simulate skip remaining pages (what btn_remaining clicked triggers)
            window.active_pdf_index = len(window.active_pdf_pages)
            window.load_next_batch_item()
            
            # Wait for thread and process events
            worker = getattr(window, "_pdf_finalize_worker", None)
            if worker:
                while worker.isRunning():
                    QApplication.processEvents()
            
            # Verify built_outputs has 3 items
            self.assertEqual(len(built_outputs), 3)
            # Verify page 0 got redacted (has a temp file output path)
            self.assertNotEqual(built_outputs[0], "page0.png")
            # Verify page 1 and 2 remained original
            self.assertEqual(built_outputs[1], "page1.png")
            self.assertEqual(built_outputs[2], "page2.png")
        finally:
            PDFHandler.build_pdf = original_build_pdf

if __name__ == "__main__":
    unittest.main()
