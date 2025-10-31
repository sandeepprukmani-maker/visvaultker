import os
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

def get_encryption_key():
    secret_key = os.environ.get('SESSION_SECRET', 'default-secret-key-please-change')
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'jira_ac_salt_v1',
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key

def encrypt_password(password):
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return encrypted.decode()
    except Exception as e:
        logging.error(f"Encryption error: {e}")
        return None

def decrypt_password(encrypted_password):
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        logging.error(f"Decryption error: {e}")
        return None
