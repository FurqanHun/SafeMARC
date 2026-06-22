import sys
import unittest
from PySide6.QtWidgets import QApplication

from src.gui.main_window import SafeMARCMainWindow


class TestUICaching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_manual_file_selection_caching(self):
        class MockScanner:
            _scan_cache = {}
            def clear_cache(self):
                pass
            def redact(self, path, out, hits):
                return True
        
        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem
        item1 = QListWidgetItem("test1.jpg")
        item1.setData(Qt.UserRole, "test1.jpg")
        item2 = QListWidgetItem("test2.jpg")
        item2.setData(Qt.UserRole, "test2.jpg")
        
        window.file_list.addItem(item1)
        window.file_list.addItem(item2)
        
        from src.core.types import SensitiveHit
        hit = SensitiveHit(10, 10, 20, 20, "FACE", 0.9)
        window.scanner._scan_cache["test1.jpg"] = [hit]
        window.user_selections_cache["test1.jpg"] = {
            "active_hits": [hit],
            "reviewed": True
        }
        
        # Select item.
        window.on_file_selected(item1)
        
        # Verify hits are loaded and populated from cache.
        self.assertEqual(window.current_file_path, "test1.jpg")
        self.assertEqual(len(window.current_hits), 1)
        self.assertEqual(window.current_hits[0].x, 10)
        self.assertEqual(window.preview_widget.active_hits, [hit])

    def test_manual_file_selection_no_scan(self):
        class MockScanner:
            _scan_cache = {}
            def clear_cache(self):
                pass
            def redact(self, path, out, hits):
                return True
        
        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem
        item1 = QListWidgetItem("test1.jpg")
        item1.setData(Qt.UserRole, "test1.jpg")
        
        window.file_list.addItem(item1)
        
        from src.core.types import SensitiveHit
        hit = SensitiveHit(15, 15, 30, 30, "MANUAL", 1.0)
        window.user_selections_cache["test1.jpg"] = {
            "active_hits": [hit],
            "reviewed": True
        }
        
        # Select item.
        window.on_file_selected(item1)
        
        # Verify selection is restored without scan hits.
        self.assertEqual(window.current_file_path, "test1.jpg")
        self.assertEqual(len(window.current_hits), 0)
        self.assertEqual(window.preview_widget.active_hits, [hit])


if __name__ == "__main__":
    unittest.main()
