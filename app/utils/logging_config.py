"""
Centralized logging configuration for the application
"""
import logging
import configparser
import sys
from pathlib import Path


class LoggingConfigurator:
    """Configure logging based on config.ini settings"""
    
    def __init__(self, config_path: str = 'config/config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        
        # Get logging settings
        self.detailed_logging_enabled = self.config.getboolean('logging', 'enable_detailed_logging', fallback=False)
        self.app_log_level = self.config.get('logging', 'app_log_level', fallback='INFO')
        self.browser_use_log_level = self.config.get('logging', 'browser_use_log_level', fallback='INFO')
        self.agent_log_level = self.config.get('logging', 'agent_log_level', fallback='INFO')
        self.llm_log_level = self.config.get('logging', 'llm_log_level', fallback='INFO')
        self.playwright_log_level = self.config.get('logging', 'playwright_log_level', fallback='WARNING')
        
        self.log_llm_requests = self.config.getboolean('logging', 'log_llm_requests', fallback=False)
        self.log_llm_responses = self.config.getboolean('logging', 'log_llm_responses', fallback=False)
        self.log_browser_actions = self.config.getboolean('logging', 'log_browser_actions', fallback=False)
        self.log_page_state = self.config.getboolean('logging', 'log_page_state', fallback=False)
        self.log_performance = self.config.getboolean('logging', 'log_performance', fallback=False)
    
    def configure(self):
        """Apply logging configuration"""
        if not self.detailed_logging_enabled:
            # Simple logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(levelname)s:%(name)s:%(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            return
        
        # Detailed logging with timestamps
        log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        logging.basicConfig(
            level=getattr(logging, self.app_log_level, logging.INFO),
            format=log_format,
            datefmt=date_format,
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True  # Override any existing configuration
        )
        
        # Configure specific loggers
        logging.getLogger('app').setLevel(getattr(logging, self.app_log_level, logging.INFO))
        logging.getLogger('browser_use').setLevel(getattr(logging, self.browser_use_log_level, logging.INFO))
        logging.getLogger('Agent').setLevel(getattr(logging, self.agent_log_level, logging.INFO))
        logging.getLogger('service').setLevel(getattr(logging, self.agent_log_level, logging.INFO))
        logging.getLogger('tools').setLevel(getattr(logging, self.agent_log_level, logging.INFO))
        logging.getLogger('BrowserSession').setLevel(getattr(logging, self.browser_use_log_level, logging.INFO))
        logging.getLogger('openai').setLevel(getattr(logging, self.llm_log_level, logging.INFO))
        logging.getLogger('httpx').setLevel(getattr(logging, self.llm_log_level, logging.INFO))
        logging.getLogger('playwright').setLevel(getattr(logging, self.playwright_log_level, logging.WARNING))
        
        # Log configuration status
        root_logger = logging.getLogger()
        root_logger.info("=" * 80)
        root_logger.info("🔧 DETAILED LOGGING ENABLED")
        root_logger.info("=" * 80)
        root_logger.info(f"App Log Level: {self.app_log_level}")
        root_logger.info(f"Browser-Use Log Level: {self.browser_use_log_level}")
        root_logger.info(f"Agent Log Level: {self.agent_log_level}")
        root_logger.info(f"LLM Log Level: {self.llm_log_level}")
        root_logger.info(f"Playwright Log Level: {self.playwright_log_level}")
        root_logger.info(f"Log LLM Requests: {self.log_llm_requests}")
        root_logger.info(f"Log LLM Responses: {self.log_llm_responses}")
        root_logger.info(f"Log Browser Actions: {self.log_browser_actions}")
        root_logger.info(f"Log Page State: {self.log_page_state}")
        root_logger.info(f"Log Performance: {self.log_performance}")
        root_logger.info("=" * 80)


# Global configurator instance
_configurator = None


def get_logging_config():
    """Get the global logging configurator"""
    global _configurator
    if _configurator is None:
        _configurator = LoggingConfigurator()
    return _configurator


def should_log_llm_requests():
    """Check if LLM requests should be logged"""
    return get_logging_config().log_llm_requests


def should_log_llm_responses():
    """Check if LLM responses should be logged"""
    return get_logging_config().log_llm_responses


def should_log_browser_actions():
    """Check if browser actions should be logged"""
    return get_logging_config().log_browser_actions


def should_log_page_state():
    """Check if page state should be logged"""
    return get_logging_config().log_page_state


def should_log_performance():
    """Check if performance metrics should be logged"""
    return get_logging_config().log_performance
