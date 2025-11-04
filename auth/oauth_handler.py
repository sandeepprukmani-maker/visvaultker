"""
OAuth 2.0 Token Handler for Gateway Authentication
Handles OAuth token fetching, caching, and certificate management
"""
import os
import sys
import logging
import requests
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(override=True)  # type: ignore
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)


def enable_certs():
    """
    Enable certificate handling for secure gateway connections
    Sets SSL certificate verification and paths
    """
    cert_path = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if cert_path and os.path.exists(cert_path):
        os.environ["REQUESTS_CA_BUNDLE"] = cert_path
        os.environ["SSL_CERT_FILE"] = cert_path
        logging.info(f"SSL certificates enabled from: {cert_path}")
    else:
        logging.debug("No custom SSL certificate path configured")


@dataclass
class OAuthConfig:
    """
    OAuth configuration for keeping track of OAuth token config
    """
    token_url: str = field(default="")
    client_id: str = field(default="")
    client_secret: str = field(default="")
    grant_type: str = field(default="")
    scope: str = field(default="")
    
    def __post_init__(self):
        """Validate required fields"""
        if not self.token_url:
            raise ValueError("OAUTH_TOKEN_URL is required")
        if not self.client_id:
            raise ValueError("OAUTH_CLIENT_ID is required")
        if not self.client_secret:
            raise ValueError("OAUTH_CLIENT_SECRET is required")


class OAuthTokenFetcher:
    """
    Class for fetching and caching OAuth tokens
    Handles refetching before token expiry
    """
    OAUTH_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
    
    def __init__(self, oauth_config: OAuthConfig):
        """
        Initialize OAuth token fetcher
        
        Args:
            oauth_config: OAuth configuration object
        """
        self._oauth_config = oauth_config
        self._token: Optional[Dict] = None
        self._refresh_after: Optional[datetime] = None
        self.early_refresh_seconds: int = int(os.environ.get("OAUTH_EARLY_REFRESH_SECONDS", "300"))
        
    def _fetch_token(self) -> Dict:
        """
        Fetch a new OAuth token from the token endpoint
        
        Returns:
            Token response dictionary
            
        Raises:
            requests.RequestException: If token fetch fails
        """
        oauth_config = self._oauth_config
        oauth_payload = {
            "client_id": oauth_config.client_id,
            "client_secret": oauth_config.client_secret,
            "grant_type": oauth_config.grant_type,
            "scope": oauth_config.scope
        }
        
        response = requests.post(
            oauth_config.token_url,
            data=oauth_payload,
            headers=self.OAUTH_HEADERS
        )
        response.raise_for_status()
        return response.json()
    
    def get_token(self) -> Dict:
        """
        Get OAuth token, fetching if needed or cache is expired
        
        Returns:
            Token dictionary with 'access_token' and 'expires_in' keys
        """
        datetime_now = datetime.now().timestamp()
        
        if (
            self._token is None or 
            self._refresh_after is None or 
            datetime_now > self._refresh_after.timestamp()
        ):
            self._token = self._fetch_token()
            
            expires_in = int(self._token.get("expires_in", 3600))
            self._refresh_after = datetime.now() + timedelta(
                seconds=(expires_in - self.early_refresh_seconds)
            )
            
            logging.info(f"OAuth token refreshed. Expires in {expires_in}s, will refresh after {self.early_refresh_seconds}s")
        
        return self._token


class OAuthTokenManager:
    """
    Singleton manager for OAuth tokens
    Ensures token fetcher persists across requests for proper caching
    """
    _instance: Optional['OAuthTokenManager'] = None
    _lock: Optional[threading.Lock] = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the token manager (only once)"""
        if self._initialized:
            return
        
        self._token_fetcher: Optional[OAuthTokenFetcher] = None
        self._initialized = True
        
    def _initialize_fetcher(self):
        """Initialize the OAuth token fetcher with configuration from environment"""
        enable_certs()
        
        required_env_vars = {
            "OAUTH_TOKEN_URL": os.environ.get("OAUTH_TOKEN_URL"),
            "OAUTH_CLIENT_ID": os.environ.get("OAUTH_CLIENT_ID"),
            "OAUTH_CLIENT_SECRET": os.environ.get("OAUTH_CLIENT_SECRET"),
            "OAUTH_GRANT_TYPE": os.environ.get("OAUTH_GRANT_TYPE"),
            "OAUTH_SCOPE": os.environ.get("OAUTH_SCOPE")
        }
        
        missing_vars = [var for var, val in required_env_vars.items() if not val]
        if missing_vars:
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        oauth_config = OAuthConfig(
            token_url=str(required_env_vars["OAUTH_TOKEN_URL"]),
            client_id=str(required_env_vars["OAUTH_CLIENT_ID"]),
            client_secret=str(required_env_vars["OAUTH_CLIENT_SECRET"]),
            grant_type=str(required_env_vars["OAUTH_GRANT_TYPE"]),
            scope=str(required_env_vars["OAUTH_SCOPE"])
        )
        
        self._token_fetcher = OAuthTokenFetcher(oauth_config)
        logging.info("OAuth token fetcher initialized")
    
    def get_token(self, max_retries: int = 3) -> str:
        """
        Get OAuth access token with retry logic and caching
        Thread-safe singleton ensures token cache persists across requests
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            OAuth access token string
            
        Raises:
            Exception: If all retry attempts fail
        """
        if self._lock is not None:
            with self._lock:
                if self._token_fetcher is None:
                    self._initialize_fetcher()
        else:
            if self._token_fetcher is None:
                self._initialize_fetcher()
        
        for attempt in range(1, max_retries + 1):
            try:
                token = self._token_fetcher.get_token()  # type: ignore
                return token["access_token"]
            except Exception as e:
                if attempt == max_retries:
                    logging.error(f"OAuth token fetch failed after {max_retries} attempts: {e}")
                    raise
                logging.warning(f"OAuth token fetch attempt {attempt} failed: {e}. Retrying...")
        
        raise Exception("Failed to fetch OAuth token")


def get_oauth_token_with_retry(max_retries: int = 3) -> str:
    """
    Get OAuth access token with retry logic
    Uses singleton token manager to ensure tokens are cached across requests
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        OAuth access token string
        
    Raises:
        Exception: If all retry attempts fail
    """
    manager = OAuthTokenManager()
    return manager.get_token(max_retries)
