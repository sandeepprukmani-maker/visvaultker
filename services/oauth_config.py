import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OauthConfig:
    """Class for keeping track of OAuth token config."""
    token_url: str = field(default="")
    client_id: str = field(default="")
    client_secret: str = field(default="")
    grant_type: str = field(default="")
    scope: str = field(default="")
    early_refresh_seconds: int = field(default=300, repr=False)
    
    def __post_init__(self):
        """Validate required fields."""
        required_fields = ["token_url", "client_id", "client_secret"]
        missing_fields = [f for f in required_fields if not getattr(self, f)]
        if missing_fields:
            raise ValueError(f"Missing required OAuth fields: {', '.join(missing_fields)}")
    
    def get_refresh_seconds(self) -> int:
        """Get early refresh token before 'expires_in'."""
        return max(1, min(self.early_refresh_seconds, 600))
    
    def get_token_payload(self) -> dict:
        """Build the OAuth token request payload."""
        return {k: v for k, v in {
            "grant_type": self.grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": self.scope,
        }.items() if v}


@dataclass
class OauthTokenFetcher:
    """Class for fetching and caching OAuth tokens. Handles refetching before token expires."""
    refresh_after: int = 0
    OAUTH_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
    
    def __init__(self, oauth_config: OauthConfig):
        self._oauth_config = oauth_config
        self._token: Optional[str] = None
        self._refresh_after = 0
    
    def _fetch_token(self) -> str:
        """Fetch a new OAuth token from the token endpoint."""
        import requests
        from datetime import datetime
        
        response = requests.post(
            self._oauth_config.token_url,
            data=self._oauth_config.get_token_payload(),
            headers=self.OAUTH_HEADERS,
        )
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("No access_token in OAuth response")
        
        expires_in = token_data.get("expires_in", 3600)
        self._refresh_after = datetime.now().timestamp() + expires_in - self._oauth_config.get_refresh_seconds()
        
        return access_token
    
    def get_token(self) -> str:
        """Get cached OAuth token. Refetch if expired."""
        from datetime import datetime
        
        if datetime.now().timestamp() > self._refresh_after:
            self._token = self._fetch_token()
        
        if not self._token:
            raise ValueError("Failed to retrieve OAuth token")
        
        return self._token
