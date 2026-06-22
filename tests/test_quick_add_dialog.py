import sys
import os
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.gui.main_window import SafeMARCMainWindow, QuickAddIdentityDialog
from src.core.types import SensitiveHit


class TestQuickAddDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication(sys.argv)

    def test_quick_add_dialog_instantiation(self):
        names = ["Alice", "Bob", "Charlie"]
        dialog = QuickAddIdentityDialog(names)
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.combo_name.count(), 3)
        self.assertEqual(dialog.combo_name.itemText(0), "Alice")
        dialog.deleteLater()

    def test_quick_add_dialog_save_logic(self):
        names = ["Alice", "Bob"]
        dialog = QuickAddIdentityDialog(names)
        dialog.combo_name.setCurrentText("Charlie")
        # Simulate click save
        dialog._on_save()
        self.assertEqual(dialog.get_name(), "Charlie")
        dialog.deleteLater()

    def test_quick_add_dialog_empty_name(self):
        dialog = QuickAddIdentityDialog([])
        dialog.combo_name.setCurrentText("   ")
        # Mock warning dialog to avoid blocking
        from unittest.mock import patch
        with patch('PySide6.QtWidgets.QMessageBox.warning') as mock_warn:
            dialog._on_save()
            self.assertTrue(mock_warn.called)
        dialog.deleteLater()
