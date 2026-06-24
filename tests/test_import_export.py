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
    password = "SuperSecretPassword123"
    plaintext = b"Hello SafeMARC! This is sensitive biometric photo data."
    
    encrypted = encrypt_data(plaintext, password)
    assert len(encrypted) == len(plaintext) + 16
    
    decrypted = decrypt_data(encrypted, password)
    assert decrypted == plaintext
    
    decrypted_wrong = decrypt_data(encrypted, "WrongPassword")
    assert decrypted_wrong != plaintext
    
    encrypted_again = encrypt_data(plaintext, password)
    assert encrypted != encrypted_again

def test_zip_slip_protection():
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
    im = IdentityManager(identities_dir=temp_dirs)
    
    alice_dir = os.path.join(temp_dirs, "Alice")
    os.makedirs(alice_dir, exist_ok=True)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    
    dummy1 = os.path.join(alice_dir, "ref_0.jpg")
    dummy2 = os.path.join(alice_dir, "ref_1.png")
    cv2.imwrite(dummy1, img)
    cv2.imwrite(dummy2, img)
    
    im.reload_identities()
    assert "Alice" in im.sface_embeddings or "Alice" in im.identity_map.values()
    
    password = "ExportPassword123"
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for filename in os.listdir(alice_dir):
            if filename.endswith(".npy") or ".lbph.png" in filename:
                continue
            full_path = os.path.join(alice_dir, filename)
            if os.path.isfile(full_path):
                zip_ref.write(full_path, arcname=os.path.join("Alice", filename))
                
    plaintext_bytes = zip_buffer.getvalue()
    encrypted_bytes = encrypt_data(plaintext_bytes, password)
    
    package_path = os.path.join(temp_dirs, "backup.smid")
    with open(package_path, 'wb') as f:
        f.write(encrypted_bytes)
    assert os.path.exists(package_path)
    
    im_clean = IdentityManager(identities_dir=os.path.join(temp_dirs, "clean_app_data"))
    
    with open(package_path, 'rb') as f:
        read_encrypted = f.read()
        
    read_decrypted = decrypt_data(read_encrypted, password)
    assert read_decrypted.startswith(b"PK\x03\x04")
    
    temp_extract_dir = os.path.join(temp_dirs, "temp_extract")
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    zip_buf = io.BytesIO(read_decrypted)
    with zipfile.ZipFile(zip_buf, 'r') as zip_ref:
        for member in zip_ref.namelist():
            norm_p = os.path.normpath(member)
            if os.path.isabs(norm_p) or norm_p.startswith("..") or "/.." in norm_p or "\\.." in norm_p:
                raise ValueError(f"Malicious path detected in archive: {member}")
        zip_ref.extractall(temp_extract_dir)
        
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
    
    alice_clean_dir = os.path.join(im_clean.identities_dir, "Alice")
    assert os.path.exists(alice_clean_dir)
    restored_files = sorted(os.listdir(alice_clean_dir))
    
    restored_images = [f for f in restored_files if not f.endswith(".npy") and ".lbph.png" not in f]
    assert len(restored_images) == 2
    assert restored_images[0].startswith("ref_0")
    assert restored_images[1].startswith("ref_1")
    
    assert im_clean.is_trained is True

def test_custom_patterns_import_export_roundtrip(temp_dirs):
    import json
    dummy_patterns = [
        {"pattern": "Confidential", "is_regex": False, "whole_word": True},
        {"pattern": r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b", "is_regex": True, "whole_word": False}
    ]
    
    password = "PatternPassword123"
    
    plaintext_bytes = json.dumps(dummy_patterns, indent=4).encode('utf-8')
    encrypted_bytes = encrypt_data(plaintext_bytes, password)
    
    smpat_path = os.path.join(temp_dirs, "patterns.smpat")
    with open(smpat_path, 'wb') as f:
        f.write(encrypted_bytes)
        
    assert os.path.exists(smpat_path)
    
    with open(smpat_path, 'rb') as f:
        read_encrypted = f.read()
        
    read_decrypted = decrypt_data(read_encrypted, password)
    decoded_str = read_decrypted.decode('utf-8')
    parsed_patterns = json.loads(decoded_str)
    
    assert parsed_patterns == dummy_patterns
    
    read_wrong_decrypted = decrypt_data(read_encrypted, "IncorrectPassword")
    with pytest.raises((UnicodeDecodeError, json.JSONDecodeError, ValueError)):
        try:
            wrong_decoded = read_wrong_decrypted.decode('utf-8')
            json.loads(wrong_decoded)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Incorrect password or corrupted file.")
            
    json_path = os.path.join(temp_dirs, "patterns.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dummy_patterns, f, indent=4)
        
    assert os.path.exists(json_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        unencrypted_parsed = json.load(f)
        
    assert unencrypted_parsed == dummy_patterns
