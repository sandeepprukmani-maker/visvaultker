"""
Flexible Model Provider Factory
Supports multiple AI providers: OpenAI, Anthropic, Gemini, and OAuth Gateway
"""
import os
import logging
import configparser
from typing import Any, Optional, Dict
from dotenv import load_dotenv
from app.utils.openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)

load_dotenv(override=True)


class ModelProviderFactory:
    """
    Factory for creating AI model clients based on configuration
    Supports: OpenAI, Anthropic, Gemini, and OAuth Gateway
    """
    
    SUPPORTED_PROVIDERS = ['openai', 'anthropic', 'gemini', 'oauth_gateway']
    
    @staticmethod
    def get_provider_config(config_path: str = 'config/config.ini') -> Dict[str, Any]:
        """
        Read provider configuration from config file
        
        Returns:
            Dictionary with provider settings
        """
        config = configparser.ConfigParser()
        config.read(config_path)
        
        provider = config.get('model_provider', 'provider', fallback='oauth_gateway')
        model = config.get('model_provider', 'model', fallback='gpt-4o')
        timeout = int(config.get('model_provider', 'timeout', fallback='90'))
        temperature = float(config.get('model_provider', 'temperature', fallback='0.7'))
        
        return {
            'provider': provider,
            'model': model,
            'timeout': timeout,
            'temperature': temperature
        }
    
    @staticmethod
    def create_llm_client(config_path: str = 'config/config.ini', for_browser_use: bool = True) -> Any:
        """
        Create an LLM client based on configuration
        
        Args:
            config_path: Path to configuration file
            for_browser_use: If True, returns langchain chat model for browser_use.Agent
                           If False, returns OpenAI-compatible adapter for playwright_mcp
        
        Returns:
            Configured LLM client
        """
        provider_config = ModelProviderFactory.get_provider_config(config_path)
        provider = provider_config['provider'].lower()
        
        if provider not in ModelProviderFactory.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider}. Must be one of {ModelProviderFactory.SUPPORTED_PROVIDERS}")
        
        logger.info(f"🤖 Initializing {provider} provider with model: {provider_config['model']}")
        
        if provider == 'openai':
            client = ModelProviderFactory._create_openai_client(provider_config, for_browser_use)
        elif provider == 'anthropic':
            client = ModelProviderFactory._create_anthropic_client(provider_config, for_browser_use)
        elif provider == 'gemini':
            client = ModelProviderFactory._create_gemini_client(provider_config, for_browser_use)
        elif provider == 'oauth_gateway':
            client = ModelProviderFactory._create_oauth_gateway_client(provider_config, for_browser_use)
        else:
            raise ValueError(f"Provider {provider} not implemented")
        
        # For playwright_mcp (for_browser_use=False), wrap langchain models with OpenAI adapter
        if not for_browser_use and hasattr(client, 'invoke'):
            logger.info("🔧 Wrapping langchain model with OpenAI adapter for playwright_mcp compatibility")
            return OpenAIAdapter(client)
        
        return client
    
    @staticmethod
    def _create_openai_client(config: Dict[str, Any], for_browser_use: bool) -> Any:
        """Create OpenAI client using langchain ChatOpenAI for universal compatibility"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
        
        from langchain_openai import ChatOpenAI
        logger.info(f"✅ OpenAI client created (ChatOpenAI) - Model: {config['model']}")
        return ChatOpenAI(
            model=config['model'],
            api_key=api_key,
            temperature=config['temperature'],
            timeout=config['timeout']
        )
    
    @staticmethod
    def _create_anthropic_client(config: Dict[str, Any], for_browser_use: bool) -> Any:
        """Create Anthropic client using langchain ChatAnthropic for universal compatibility"""
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
        
        from langchain_anthropic import ChatAnthropic
        logger.info(f"✅ Anthropic client created (ChatAnthropic) - Model: {config['model']}")
        return ChatAnthropic(
            model=config['model'],
            api_key=api_key,
            temperature=config['temperature'],
            timeout=config['timeout']
        )
    
    @staticmethod
    def _create_gemini_client(config: Dict[str, Any], for_browser_use: bool) -> Any:
        """Create Google Gemini client using langchain ChatGoogleGenerativeAI for universal compatibility"""
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini provider")
        
        from langchain_google_genai import ChatGoogleGenerativeAI
        logger.info(f"✅ Gemini client created (ChatGoogleGenerativeAI) - Model: {config['model']}")
        # Note: ChatGoogleGenerativeAI doesn't support timeout parameter
        return ChatGoogleGenerativeAI(
            model=config['model'],
            google_api_key=api_key,
            temperature=config['temperature']
        )
    
    @staticmethod
    def _create_oauth_gateway_client(config: Dict[str, Any], for_browser_use: bool) -> Any:
        """Create OAuth Gateway client (existing implementation)"""
        from auth.oauth_handler import get_oauth_token_with_retry
        
        gateway_base_url = os.environ.get('GW_BASE_URL')
        if not gateway_base_url:
            raise ValueError("GW_BASE_URL environment variable is required for OAuth Gateway provider")
        
        try:
            oauth_token = get_oauth_token_with_retry(max_retries=3)
        except Exception as e:
            raise ValueError(f"Failed to obtain OAuth token: {str(e)}. Please check your OAuth configuration.")
        
        if for_browser_use:
            from langchain_openai import ChatOpenAI
            logger.info(f"✅ OAuth Gateway client created (ChatOpenAI) - Model: {config['model']} via {gateway_base_url}")
            return ChatOpenAI(
                model=config['model'],
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={
                    "Authorization": f"Bearer {oauth_token}"
                },
                timeout=config['timeout']
            )
        else:
            from openai import OpenAI
            logger.info(f"✅ OAuth Gateway client created (OpenAI) - Model: {config['model']} via {gateway_base_url}")
            return OpenAI(
                base_url=gateway_base_url,
                api_key=oauth_token,
                default_headers={
                    "Authorization": f"Bearer {oauth_token}"
                }
            )
    
    @staticmethod
    def get_required_env_vars(provider: str) -> list:
        """
        Get list of required environment variables for a provider
        
        Args:
            provider: Provider name
            
        Returns:
            List of required environment variable names
        """
        env_vars_map = {
            'openai': ['OPENAI_API_KEY'],
            'anthropic': ['ANTHROPIC_API_KEY'],
            'gemini': ['GOOGLE_API_KEY'],
            'oauth_gateway': [
                'OAUTH_TOKEN_URL',
                'OAUTH_CLIENT_ID',
                'OAUTH_CLIENT_SECRET',
                'OAUTH_GRANT_TYPE',
                'OAUTH_SCOPE',
                'GW_BASE_URL'
            ]
        }
        return env_vars_map.get(provider.lower(), [])
    
    @staticmethod
    def validate_provider_config(provider: Optional[str] = None) -> tuple[bool, list]:
        """
        Validate that required environment variables are set for the configured provider
        
        Args:
            provider: Provider name, or None to read from config
            
        Returns:
            Tuple of (is_valid, missing_vars)
        """
        if provider is None:
            provider_config = ModelProviderFactory.get_provider_config()
            provider = provider_config['provider']
        
        required_vars = ModelProviderFactory.get_required_env_vars(provider)
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        return (len(missing_vars) == 0, missing_vars)
