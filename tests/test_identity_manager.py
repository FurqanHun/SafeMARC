import os
import tempfile
import shutil
import pytest
import cv2
import numpy as np
from src.core.identity_manager import IdentityManager


@pytest.fixture
def temp_dirs(monkeypatch):
    # Set up temporary directory for identity manager data.
    temp_dir = tempfile.mkdtemp()
    # Mock tempfile.gettempdir() to isolate the session_temp directory.
    monkeypatch.setattr(tempfile, "gettempdir", lambda: temp_dir)
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_identity_manager_initialization(temp_dirs):
    im = IdentityManager(identities_dir=temp_dirs)
    
    assert im.identities_dir == os.path.abspath(temp_dirs)
    assert os.path.exists(im.identities_dir)
    assert os.path.exists(im.session_temp)
    assert isinstance(im.identity_map, dict)
    assert im.is_trained is False


def test_add_session_identity(temp_dirs):
    im = IdentityManager(identities_dir=temp_dirs)
    
    # Create a dummy image.
    dummy_img_path = os.path.join(temp_dirs, "dummy.jpg")
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(dummy_img_path, img)
    
    # Add session identity (temporary).
    im.add_session_identity("Alice", dummy_img_path)
    
    # Check that Alice directory was created in session_temp.
    alice_dir = os.path.join(im.session_temp, "Alice")
    assert os.path.exists(alice_dir)
    assert len(os.listdir(alice_dir)) > 0
    
    # Cleanup dummy image.
    os.remove(dummy_img_path)


def test_add_permanent_identity(temp_dirs):
    im = IdentityManager(identities_dir=temp_dirs)
    
    # Create dummy images.
    dummy1 = os.path.join(temp_dirs, "dummy1.jpg")
    dummy2 = os.path.join(temp_dirs, "dummy2.jpg")
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(dummy1, img)
    cv2.imwrite(dummy2, img)
    
    # Add permanent identity.
    im.add_identity("Bob", [dummy1, dummy2])
    
    # Check that Bob directory was created in permanent identities_dir.
    bob_dir = os.path.join(im.identities_dir, "Bob")
    assert os.path.exists(bob_dir)
    assert len(os.listdir(bob_dir)) > 0
    
    os.remove(dummy1)
    os.remove(dummy2)
