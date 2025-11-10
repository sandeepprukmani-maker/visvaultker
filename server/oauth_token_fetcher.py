import sys
import os
import httpx
import logging
from dotenv import load_dotenv
from typing import Optional, Any, Dict, List
from datetime import datetime
from dataclasses import dataclass, field, asdict

@dataclass
class OAuthConfig:
    """Class for keeping track of OAuth token configs."""
    token_url: str = field(repr=False)
    client_id: str
    client_secret: str
    grant_type: str
    scope: str
    early_refresh_seconds: int = field(default=300, repr=False)
    
    def oauth_payload(self) -> dict:
        return {k: v for k, v in asdict(self).items()
                if k != 'self' and k in self.__dataclass_fields__ and self.__dataclass_fields__[k].repr}

class OAuthTokenFetcher:
    """Class for fetching and caching an OAuth token. Handles refetching before token expires"""
    OAUTH_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

    def __init__(self, oauth_config: OAuthConfig) -> None:
        self._oauth_config = oauth_config
        self._fetch_token()

    def _fetch_token(self) -> str:
        response = httpx.post(
            url=self._oauth_config.token_url,
            data=self._oauth_config.oauth_payload(),
            headers=self.OAUTH_HEADERS
        )
        response.raise_for_status()
        self._token = response.json()
        self.refresh_after = (
            datetime.now().timestamp() +
            self._token["expires_in"] -
            self._oauth_config.early_refresh_seconds
        )
        return self._token

    def get_token(self) -> str:
        if datetime.now().timestamp() > self.refresh_after:
            self._fetch_token()
        return self._token["access_token"]

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)

def _ensure_env_vars_for_oauth():
    required_env_vars = [
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID",
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE",
        "GW_BASE_URL",
    ]
    missing = [v for v in required_env_vars if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

_token_fetcher: Optional[OAuthTokenFetcher] = None

def _get_token_fetcher() -> OAuthTokenFetcher:
    global _token_fetcher
    if _token_fetcher is None:
        _ensure_env_vars_for_oauth()
        oauth_config = OAuthConfig(
            token_url=os.environ["OAUTH_TOKEN_URL"],
            client_id=os.environ["OAUTH_CLIENT_ID"],
            client_secret=os.environ["OAUTH_CLIENT_SECRET"],
            grant_type=os.environ["OAUTH_GRANT_TYPE"],
            scope=os.environ["OAUTH_SCOPE"],
        )
        _token_fetcher = OAuthTokenFetcher(oauth_config)
    return _token_fetcher

def get_access_token() -> str:
    """Return an OAuth access token string using the Gen AI Gateway OAuth helper."""
    fetcher = _get_token_fetcher()
    token = fetcher.get_token()
    return str(token)

if __name__ == "__main__":
    try:
        token = get_access_token()
        print(token)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
