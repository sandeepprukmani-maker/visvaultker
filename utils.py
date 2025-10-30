from cryptography.fernet import Fernet
import os
import base64
import hashlib

def get_encryption_key():
    key = os.environ.get('ENCRYPTION_KEY')
    if key:
        return key.encode() if isinstance(key, str) else key
    
    session_secret = os.environ.get('SESSION_SECRET', 'dev-secret-key-please-change-in-production')
    hashed = hashlib.sha256(session_secret.encode()).digest()
    return base64.urlsafe_b64encode(hashed)

def encrypt_password(password):
    if not password:
        return None
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(password.encode()).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

def decrypt_password(encrypted_password):
    if not encrypted_password:
        return None
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(encrypted_password.encode()).decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return None
