"""
Secure Credential Manager for Website Logins
Handles encrypted storage and retrieval of user credentials
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
from cryptography.fernet import Fernet
import os
import base64
import hashlib

class WebsiteCredential(Base):
    """Encrypted credentials for website logins"""
    __tablename__ = "website_credentials"
    
    id = Column(String, primary_key=True)
    website_profile_id = Column(String, ForeignKey("website_profiles.id"), nullable=False)
    
    credential_name = Column(String, nullable=False)
    encrypted_username = Column(Text, nullable=False)
    encrypted_password = Column(Text, nullable=False)
    
    login_url = Column(String, nullable=True)
    username_selector = Column(String, nullable=True)
    password_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CredentialManager:
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher = Fernet(self.encryption_key)
    
    def _get_encryption_key(self) -> bytes:
        """
        Get encryption key from environment variable
        
        Raises:
            RuntimeError: If CREDENTIAL_ENCRYPTION_KEY is not set
        """
        key_env = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
        
        if not key_env:
            raise RuntimeError(
                "CREDENTIAL_ENCRYPTION_KEY environment variable is required for secure credential storage.\n"
                "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'\n"
                "Then set it as an environment variable."
            )
        
        try:
            # Validate key format
            return key_env.encode()
        except Exception as e:
            raise RuntimeError(f"Invalid CREDENTIAL_ENCRYPTION_KEY format: {e}")
    
    def encrypt_credential(self, value: str) -> str:
        """Encrypt a credential value"""
        encrypted = self.cipher.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_credential(self, encrypted_value: str) -> str:
        """Decrypt a credential value"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode()
    
    def store_credentials(
        self,
        profile_id: str,
        credential_name: str,
        username: str,
        password: str,
        login_url: str = None,
        selectors: dict = None
    ) -> dict:
        """Store encrypted credentials for a website"""
        import uuid
        
        credential_id = str(uuid.uuid4())
        encrypted_username = self.encrypt_credential(username)
        encrypted_password = self.encrypt_credential(password)
        
        credential_data = {
            'id': credential_id,
            'website_profile_id': profile_id,
            'credential_name': credential_name,
            'encrypted_username': encrypted_username,
            'encrypted_password': encrypted_password,
            'login_url': login_url
        }
        
        if selectors:
            credential_data.update({
                'username_selector': selectors.get('username'),
                'password_selector': selectors.get('password'),
                'submit_selector': selectors.get('submit')
            })
        
        return credential_data
    
    def retrieve_credentials(self, credential_id: str, encrypted_data: dict) -> dict:
        """Retrieve and decrypt credentials"""
        return {
            'username': self.decrypt_credential(encrypted_data['encrypted_username']),
            'password': self.decrypt_credential(encrypted_data['encrypted_password']),
            'login_url': encrypted_data.get('login_url'),
            'selectors': {
                'username': encrypted_data.get('username_selector'),
                'password': encrypted_data.get('password_selector'),
                'submit': encrypted_data.get('submit_selector')
            }
        }


credential_manager = CredentialManager()
