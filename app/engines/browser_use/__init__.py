"""
Browser-Use Codebase
AI-powered browser automation using browser-use library with LLM reasoning
"""
from app.engines.browser_use.engine_optimized import OptimizedBrowserUseEngine


def create_engine(headless: bool = False):
    """
    Factory function to create an optimized Browser-Use engine instance
    
    The engine will automatically select the appropriate LLM model based on config.ini:
    - If use_chat_browser_use=true, uses ChatBrowserUse (3-5x faster)
    - Otherwise uses standard OpenAI models
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        OptimizedBrowserUseEngine instance with advanced features enabled
    """
    return OptimizedBrowserUseEngine(headless=headless, enable_advanced_features=True)


__all__ = ['OptimizedBrowserUseEngine', 'create_engine']
