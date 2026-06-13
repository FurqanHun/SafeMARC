import os
import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QKeySequence

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui.main_window import SafeMARCMainWindow
from gui.settings_dialog import SettingsDialog, DEFAULT_SHORTCUTS, SHORTCUT_METADATA


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
        # Instantiate main window (using a mock scanner to avoid running actual ML model loads)
        class MockScanner:
            identity_manager = None
            def clear_cache(self):
                pass

        window = SafeMARCMainWindow()
        # Mock scanner to speed up and avoid actual MediaPipe initialization in simple GUI test
        window.scanner = MockScanner()
        
        # Initially check draw shortcut sequence is default ("D")
        self.assertEqual(window.shortcut_draw.key().toString(), "D")
        
        # Dynamically change shortcut
        window.update_shortcut_key("toggle_draw", "Ctrl+D")
        
        # Verify it updated in the config dict and QShortcut object
        self.assertEqual(window.shortcuts_config["toggle_draw"], "Ctrl+D")
        self.assertEqual(window.shortcut_draw.key().toString(), "Ctrl+D")
        
        # Reset back to default
        window.update_shortcut_key("toggle_draw", "D")
        self.assertEqual(window.shortcut_draw.key().toString(), "D")


if __name__ == "__main__":
    unittest.main()
