import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.append('.')
sys.path.append('..')

from services.oauth_config import OauthConfig, OauthTokenFetcher
from openai import OpenAI

logging.basicConfig(level=logging.INFO)


def send_gpt_request(prompt: str, maxtoken: int = 4000, temperature: float = 0.7) -> str:
    """Send a GPT request using OAuth authentication."""
    if not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")
    if not isinstance(maxtoken, int):
        raise ValueError("maxtoken must be a non-empty string.")
    
    required_env_vars = {
        "OAUTH_TOKEN_URL",
        "OAUTH_CLIENT_ID", 
        "OAUTH_CLIENT_SECRET",
        "OAUTH_GRANT_TYPE",
        "OAUTH_SCOPE"
    }
    
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    enable_certs()
    oauth_config = OauthConfig(
        token_url=os.environ["OAUTH_TOKEN_URL"],
        client_id=os.environ["OAUTH_CLIENT_ID"],
        client_secret=os.environ["OAUTH_CLIENT_SECRET"],
        grant_type=os.environ["OAUTH_GRANT_TYPE"],
        scope=os.environ["OAUTH_SCOPE"]
    )
    
    token_fetcher = OauthTokenFetcher(oauth_config)
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            base_url = os.environ.get("GPT_BASE_URL")
            if base_url:
                client = OpenAI(
                    api_key=token_fetcher.get_token(),
                    base_url=base_url
                )
            else:
                client = OpenAI(api_key=token_fetcher.get_token())
            
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


def enable_certs():
    """Enable SSL certificates if needed."""
    import certifi
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    os.environ['SSL_CERT_FILE'] = certifi.where()
