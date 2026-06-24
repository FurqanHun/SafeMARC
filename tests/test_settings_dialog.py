import sys
import os
import tempfile
import shutil
import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QInputDialog
from unittest.mock import patch

from src.gui.settings_dialog import SettingsDialog
from src.core.identity_manager import IdentityManager


class MockScanner:
    def __init__(self, identity_manager):
        self.identity_manager = identity_manager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def temp_dirs(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: temp_dir)
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_settings_dialog_rename(qapp, temp_dirs):
    identities_dir = os.path.join(temp_dirs, "identities_storage")
    os.makedirs(identities_dir, exist_ok=True)
    
    im = IdentityManager(identities_dir=identities_dir)
    
    # Create Bob
    bob_dir = os.path.join(identities_dir, "Bob")
    os.makedirs(bob_dir, exist_ok=True)
    im.reload_identities()
    
    scanner = MockScanner(im)
    dialog = SettingsDialog(scanner)
    assert dialog is not None
    
    # Verify Bob is in the list
    assert dialog.list_people.count() == 1
    item = dialog.list_people.item(0)
    assert item.text() == "Bob"
    
    # Select Bob
    dialog.list_people.setCurrentItem(item)
    assert dialog.btn_rename_person.isEnabled() is True
    
    # Mock QInputDialog to return "Robert"
    with patch.object(QInputDialog, 'getText', return_value=("Robert", True)):
        dialog._rename_person()
        
    # Verify directory was renamed on disk
    assert not os.path.exists(os.path.join(identities_dir, "Bob"))
    assert os.path.exists(os.path.join(identities_dir, "Robert"))
    
    # Verify people list and list_people widget updated
    assert dialog.list_people.count() == 1
    assert dialog.list_people.item(0).text() == "Robert"
    
    dialog.deleteLater()
