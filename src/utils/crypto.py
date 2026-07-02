import os
import hashlib
import logging
logger = logging.getLogger(__name__)

def encrypt_data(data: bytes, password: str) -> bytes:
    """
    Encrypts arbitrary binary payload using PBKDF2-HMAC-SHA256 key derivation
    and a custom Counter (CTR) mode stream cipher driven by SHA-256.
    """
    logger.debug(f"Encrypting {len(data)} bytes of data")
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    ciphertext = bytearray(len(data))
    block_size = 32
    num_blocks = (len(data) + block_size - 1) // block_size
    
    for i in range(num_blocks):
        counter_bytes = i.to_bytes(4, 'big')
        keystream = hashlib.sha256(key + counter_bytes).digest()
        
        start = i * block_size
        end = min(start + block_size, len(data))
        for j in range(start, end):
            ciphertext[j] = data[j] ^ keystream[j - start]
            
    return salt + bytes(ciphertext)

def decrypt_data(encrypted_data: bytes, password: str) -> bytes:
    """
    Decrypts a binary payload encrypted via PBKDF2-HMAC-SHA256 key derivation
    and a Counter (CTR) mode stream cipher.
    """
    logger.debug(f"Decrypting {len(encrypted_data)} bytes of data")
    if len(encrypted_data) < 16:
        raise ValueError("Invalid encrypted data length.")
        
    salt = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    
    plaintext = bytearray(len(ciphertext))
    block_size = 32
    num_blocks = (len(ciphertext) + block_size - 1) // block_size
    
    for i in range(num_blocks):
        counter_bytes = i.to_bytes(4, 'big')
        keystream = hashlib.sha256(key + counter_bytes).digest()
        
        start = i * block_size
        end = min(start + block_size, len(ciphertext))
        for j in range(start, end):
            plaintext[j] = ciphertext[j] ^ keystream[j - start]
            
    return bytes(plaintext)
