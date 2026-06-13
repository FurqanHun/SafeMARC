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


if __name__ == "__main__":
    unittest.main()
