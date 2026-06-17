import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeySequence

from src.gui.main_window import SafeMARCMainWindow
from src.gui.settings_dialog import DEFAULT_SHORTCUTS, SHORTCUT_METADATA


class TestShortcutSettings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_default_shortcuts_exist(self):
        self.assertIn("toggle_draw", DEFAULT_SHORTCUTS)
        self.assertEqual(DEFAULT_SHORTCUTS["toggle_draw"], "D")
        self.assertIn("toggle_persistent", DEFAULT_SHORTCUTS)

    def test_dynamic_shortcut_update(self):
        class MockScanner:
            identity_manager = None
            def clear_cache(self):
                pass

        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        
        self.assertEqual(window.shortcut_draw.key().toString(), "D")
        
        window.update_shortcut_key("toggle_draw", "Ctrl+D")
        
        self.assertEqual(window.shortcuts_config["toggle_draw"], "Ctrl+D")
        self.assertEqual(window.shortcut_draw.key().toString(), "Ctrl+D")
        
        window.update_shortcut_key("toggle_draw", "D")
        self.assertEqual(window.shortcut_draw.key().toString(), "D")

    def test_settings_dialog_instantiation(self):
        class MockScanner:
            identity_manager = None
            def clear_cache(self):
                pass
        window = SafeMARCMainWindow()
        window.scanner = MockScanner()
        
        from src.gui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(window.scanner, window)
        self.assertIsNotNone(dialog)
        dialog.deleteLater()

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
        
        # Manually select the item
        window.on_file_selected(item1)
        
        # Verify that the hits are loaded from the cache and populated
        self.assertEqual(window.current_file_path, "test1.jpg")
        self.assertEqual(len(window.current_hits), 1)
        self.assertEqual(window.current_hits[0].x, 10)
        self.assertEqual(window.preview_widget.active_hits, [hit])


if __name__ == "__main__":
    unittest.main()
