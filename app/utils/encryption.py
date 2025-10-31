"""
Encryption utilities for securely storing sensitive credentials
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class CredentialEncryption:
    """
    Handles encryption and decryption of stored credentials.
    Uses Fernet (symmetric encryption) with a key derived from an environment variable.
    """
    
    def __init__(self):
        self._cipher = None
        
    def _get_cipher(self):
        """
        Get or create the Fernet cipher instance.
        Requires ENCRYPTION_KEY environment variable to be set.
        
        The ENCRYPTION_KEY should be a base64-encoded Fernet key.
        To generate a secure key, run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        
        Raises:
            ValueError: If ENCRYPTION_KEY is not set or invalid
        """
        if self._cipher is not None:
            return self._cipher
            
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY environment variable is not set. "
                "Credential vault requires a secure encryption key. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\" "
                "Then set it as an environment variable or Replit Secret."
            )
        
        try:
            # Try to use it directly as a Fernet key
            self._cipher = Fernet(encryption_key.encode())
            return self._cipher
        except Exception as e:
            raise ValueError(
                f"Invalid ENCRYPTION_KEY format: {str(e)}. "
                "The key must be a valid Fernet key (44 characters, base64-encoded). "
                "Generate a new one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ''
            
        cipher = self._get_cipher()
        encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            return ''
            
        try:
            cipher = self._get_cipher()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode('utf-8'))
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")


credential_encryption = CredentialEncryption()
