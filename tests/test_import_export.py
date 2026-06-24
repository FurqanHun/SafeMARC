import os
import tempfile
import shutil
import pytest
import zipfile
import io
import cv2
import numpy as np
from src.utils.crypto import encrypt_data, decrypt_data
from src.core.identity_manager import IdentityManager

@pytest.fixture
def temp_dirs(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: temp_dir)
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def test_crypto_roundtrip():
    # Test helper cryptographic encryption/decryption functions.
    password = "SuperSecretPassword123"
    plaintext = b"Hello SafeMARC! This is sensitive biometric photo data."
    
    encrypted = encrypt_data(plaintext, password)
    assert len(encrypted) == len(plaintext) + 16 # salt (16) + CTR cipher
    
    # Correct decryption
    decrypted = decrypt_data(encrypted, password)
    assert decrypted == plaintext
    
    # Incorrect decryption (expecting different/garbage bytes)
    decrypted_wrong = decrypt_data(encrypted, "WrongPassword")
    assert decrypted_wrong != plaintext
    
    # Cryptographic integrity check (salt is random)
    encrypted_again = encrypt_data(plaintext, password)
    assert encrypted != encrypted_again # Should differ because of random salt

def test_zip_slip_protection():
    # Verify our Zip Slip path traversal checks.
    malicious_names = [
        "../escaped.png",
        "/absolute/path/hacked.jpg",
        "Alice/../../escape_parent.png",
        "Bob\\..\\..\\escape_parent.jpg"
    ]
    
    for name in malicious_names:
        normalized_path = os.path.normpath(name)
        is_malicious = (
            os.path.isabs(normalized_path) or
            normalized_path.startswith("..") or
            "/.." in normalized_path or
            "\\.." in normalized_path
        )
        assert is_malicious, f"Failed to identify malicious path traversal: {name}"

def test_export_import_roundtrip(temp_dirs):
    # Initialize identity manager
    im = IdentityManager(identities_dir=temp_dirs)
    
    # Create dummy images for identity "Alice"
    alice_dir = os.path.join(temp_dirs, "Alice")
    os.makedirs(alice_dir, exist_ok=True)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    dummy1 = os.path.join(alice_dir, "ref_0.jpg")
    dummy2 = os.path.join(alice_dir, "ref_1.png")
    cv2.imwrite(dummy1, img)
    cv2.imwrite(dummy2, img)
    
    # Reload identities
    im.reload_identities()
    assert "Alice" in im.sface_embeddings or "Alice" in im.identity_map.values()
    
    # 1. Simulate the export zipping & encrypting logic
    password = "ExportPassword123"
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        # Walk through Alice's permanent directory and add raw images
        for filename in os.listdir(alice_dir):
            if filename.endswith(".npy") or ".lbph.png" in filename:
                continue
            full_path = os.path.join(alice_dir, filename)
            if os.path.isfile(full_path):
                zip_ref.write(full_path, arcname=os.path.join("Alice", filename))
                
    plaintext_bytes = zip_buffer.getvalue()
    encrypted_bytes = encrypt_data(plaintext_bytes, password)
    
    # Verify the encrypted package file
    package_path = os.path.join(temp_dirs, "backup.smid")
    with open(package_path, 'wb') as f:
        f.write(encrypted_bytes)
    assert os.path.exists(package_path)
    
    # 2. Simulate the import decrypting & unzipping logic into a new clean environment
    im_clean = IdentityManager(identities_dir=os.path.join(temp_dirs, "clean_app_data"))
    
    # Read package
    with open(package_path, 'rb') as f:
        read_encrypted = f.read()
        
    # Decrypt and verify
    read_decrypted = decrypt_data(read_encrypted, password)
    assert read_decrypted.startswith(b"PK\x03\x04")
    
    # Secure extraction
    temp_extract_dir = os.path.join(temp_dirs, "temp_extract")
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    zip_buf = io.BytesIO(read_decrypted)
    with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
        # Zip slip check
        for member in zip_ref.namelist():
            norm_p = os.path.normpath(member)
            if os.path.isabs(norm_p) or norm_p.startswith("..") or "/.." in norm_p or "\\.." in norm_p:
                raise ValueError(f"Malicious path detected in archive: {member}")
        zip_ref.extractall(temp_extract_dir)
        
    # Copy images to im_clean using add_identity
    imported_count = 0
    for entry in os.listdir(temp_extract_dir):
        entry_path = os.path.join(temp_extract_dir, entry)
        if os.path.isdir(entry_path):
            image_files = []
            for filename in os.listdir(entry_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                    image_files.append(os.path.join(entry_path, filename))
            if image_files:
                im_clean.add_identity(entry, image_files)
                imported_count += 1
                
    assert imported_count == 1
    
    # Check that Alice was restored successfully and has her two images renamed ref_0.jpg, ref_1.png
    alice_clean_dir = os.path.join(im_clean.identities_dir, "Alice")
    assert os.path.exists(alice_clean_dir)
    restored_files = sorted(os.listdir(alice_clean_dir))
    
    # Filter out cache files
    restored_images = [f for f in restored_files if not f.endswith(".npy") and ".lbph.png" not in f]
    assert len(restored_images) == 2
    assert restored_images[0].startswith("ref_0")
    assert restored_images[1].startswith("ref_1")
    
    # Verify retraining complete
    assert im_clean.is_trained is True
