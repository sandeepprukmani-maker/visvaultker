import sys
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI

load_dotenv(override=True)

try:
    from genai_gateway_tools.oauth import OAuthConfig, OAuthTokenFetcher
    from tbc_security import enable_certs
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    logging.warning("OAuth dependencies not available. Install genai_gateway_tools and tbc_security if needed.")

logging.basicConfig(level=logging.INFO)


class GatewayLLMClient:
    """
    LLM client that uses Gen AI Gateway with OAuth authentication.
    """
    
    def __init__(self):
        self.token_fetcher = None
        self.base_url = None
        self._setup_oauth()
    
    def _setup_oauth(self):
        """Setup OAuth configuration and token fetcher."""
        if not OAUTH_AVAILABLE:
            raise ImportError("OAuth dependencies not available. Install genai_gateway_tools and tbc_security.")
        
        required_env_vars = [
            "OAUTH_TOKEN_URL",
            "OAUTH_CLIENT_ID",
            "OAUTH_CLIENT_SECRET",
            "OAUTH_GRANT_TYPE",
            "OAUTH_SCOPE",
            "GW_BASE_URL"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
        if missing_vars:
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        enable_certs()
        
        oauth_config = OAuthConfig(
            token_url=os.environ["OAUTH_TOKEN_URL"],
            client_id=os.environ["OAUTH_CLIENT_ID"],
            client_secret=os.environ["OAUTH_CLIENT_SECRET"],
            grant_type=os.environ["OAUTH_GRANT_TYPE"],
            scope=os.environ["OAUTH_SCOPE"]
        )
        
        self.token_fetcher = OAuthTokenFetcher(oauth_config)
        self.base_url = os.environ.get("GW_BASE_URL")
    
    def get_client(self) -> OpenAI:
        """Get an OpenAI client with OAuth token."""
        return OpenAI(
            api_key=self.token_fetcher.get_token(),
            base_url=self.base_url
        )
    
    def create_chat_completion(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 6000,
        temperature: float = 0.2,
        **kwargs
    ) -> Any:
        """
        Create a chat completion using the Gen AI Gateway.
        
        Args:
            model: Model name (e.g., "ms.anthropic.claude-sonnet-4-5-20250929-v1:0")
            messages: List of message dictionaries
            max_tokens: Maximum tokens in response
            temperature: Temperature for response generation
            **kwargs: Additional parameters for the API
        
        Returns:
            API response object
        """
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                client = self.get_client()
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                return response
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    raise
        
        raise Exception("Failed to get response after all retries")
    
    def create_message(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 4096,
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Any:
        """
        Create a message using Anthropic-style API format through the gateway.
        
        Args:
            model: Model name
            messages: List of messages
            max_tokens: Maximum tokens
            system: System prompt
            tools: List of tool definitions
            **kwargs: Additional parameters
        
        Returns:
            API response object
        """
        # Convert to OpenAI format if system prompt is provided
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        formatted_messages.extend(messages)
        
        max_retries = 3
        
        for attempt in range(1, max_retries + 1):
            try:
                client = self.get_client()
                
                # If tools are provided, convert to OpenAI format
                if tools:
                    openai_tools = []
                    for tool in tools:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.get("name"),
                                "description": tool.get("description", ""),
                                "parameters": tool.get("input_schema", {})
                            }
                        })
                    kwargs["tools"] = openai_tools
                
                response = client.chat.completions.create(
                    model=model,
                    messages=formatted_messages,
                    max_tokens=max_tokens,
                    **kwargs
                )
                return response
            except Exception as e:
                logging.error(f"Attempt {attempt} failed: {e}")
                if attempt == max_retries:
                    raise
        
        raise Exception("Failed to get response after all retries")
