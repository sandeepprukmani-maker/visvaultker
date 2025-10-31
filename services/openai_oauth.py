import os
import sys
import logging
from typing import Optional, Any, Dict, List
from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.append('.')
sys.path.append('..')

from services.oauth_config import OauthConfig, OauthTokenFetcher
from openai import OpenAI

logging.basicConfig(level=logging.INFO)


def _ensure_env_vars_for_oauth():
    """Check required OAuth environment variables."""
    required_env_vars = [
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID", 
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE"
    ]
    
    missing = [v for v in required_env_vars if not os.environ.get(v)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


# Lightweight cached token fetcher instance (uses genai_gateway_tools.oauth.OauthTokenFetcher which does its own refresh)
_token_fetcher: Optional[OauthTokenFetcher] = None


def _get_token_fetcher() -> OauthTokenFetcher:
    """Create and return token fetcher instance."""
    global _token_fetcher
    if _token_fetcher is None:
        _ensure_env_vars_for_oauth()
        oauth_config = OauthConfig(
            token_url=os.environ["OAUTH_TOKEN_URL"],
            client_id=os.environ["OAUTH_CLIENT_ID"],
            client_secret=os.environ["OAUTH_CLIENT_SECRET"],
            grant_type=os.environ["OAUTH_GRANT_TYPE"],
            scope=os.environ["OAUTH_SCOPE"]
        )
        _token_fetcher = OauthTokenFetcher(oauth_config)
    return _token_fetcher


def get_access_token() -> str:
    """Return an OAuth access token string using the Gen AI Gateway OAuth helper.
    
    This wraps the genai_gateway_tools.oauth.OauthTokenFetcher and is safe to call from other modules.
    
    The token from genai_gateway_tools is either a dict of a string depending on implementation: normalize
    if isinstance(token, dict):
        return token.get("access_token") or token.get("token") or str(token)
    return str(token)
    """
    fetcher = _get_token_fetcher()
    token = fetcher.get_token()
    
    # Token from genai_gateway_tools is either a dict or a string depending on implementation: normalize
    if isinstance(token, dict):
        return token.get("access_token") or token.get("token") or str(token)
    return str(token)


def create_client() -> OpenAI:
    """Create and return an OpenAI client configured with the current access token and gateway base URL."""
    token = get_access_token()
    base_uri = os.environ.get("GW_BASE_URL")
    return OpenAI(api_key=token, base_url=base_uri)


def send_chat_request(messages: List[Dict[str, Any]], model: str = "gpt-4", **kwargs) -> Any:
    """Send a chat request (list of messages) to the model via the Gen AI Gateway.
    
    Args:
        messages: List of message dicts in the OpenAI format ({"role":..., "content":..., ...})
        model: Model name to call (defaults to gpt-4)
        **kwargs: Passed through to the underlying OpenAI.chat.completions.create call (e.g., temperature, max_tokens, response_format)
    
    Returns:
        The raw response object from the OpenAI SDK. Callers may inspect .choices[0].message.content.
    """
    client = create_client()
    response = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return response


def send_gpt35_request(prompt: str) -> str:
    """Backend-compatible helper: send single-user prompt to gpt-35-turbo and return the content string."""
    if not prompt or not isinstance(prompt, str):
        logging.error("Prompt must be a non-empty string.")
        raise ValueError("Prompt must be a non-empty string.")
    
    # Simple single-message wrapper
    messages = [{"role": "user", "content": prompt}]
    response = send_chat_request(messages=messages, model="gpt-35-turbo")
    return response.choices[0].message.content


def send_gpt_request(prompt: str, maxtoken: int = 4000, temperature: float = 0.7) -> str:
    """Send a GPT request using OAuth authentication."""
    if not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")
    if not isinstance(maxtoken, int):
        raise ValueError("maxtoken must be an integer.")
    
    _ensure_env_vars_for_oauth()
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            client = create_client()
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=maxtoken,
                temperature=temperature
            )
            
            result = response.choices[0].message.content
            if result is None:
                raise ValueError("Received empty response from GPT")
            logging.info(f"GPT-4 response: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
    
    raise Exception("Failed to get GPT response after maximum retries")
