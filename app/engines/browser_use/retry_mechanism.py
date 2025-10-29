"""
Smart Retry Mechanism for Browser Automation
Implements exponential backoff and intelligent retry logic
"""
import time
import logging
import asyncio
from typing import Callable, Any, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 30.0,
                 backoff_factor: float = 2.0,
                 retry_on_exceptions: Optional[List[type]] = None):
        """
        Initialize retry configuration
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for exponential backoff
            retry_on_exceptions: List of exception types to retry on (None = all)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retry_on_exceptions = retry_on_exceptions or [Exception]


class RetryMechanism:
    """
    Smart retry handler with exponential backoff
    Handles both sync and async operations
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry mechanism
        
        Args:
            config: Retry configuration (uses defaults if None)
        """
        self.config = config or RetryConfig()
        self.retry_stats = {
            "total_attempts": 0,
            "total_retries": 0,
            "successful_retries": 0,
            "failed_operations": 0
        }
    
    def retry(self, func: Callable) -> Callable:
        """
        Decorator for synchronous functions with retry logic
        
        Args:
            func: Function to wrap with retry logic
            
        Returns:
            Wrapped function with retry capability
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    
    def async_retry(self, func: Callable) -> Callable:
        """
        Decorator for asynchronous functions with retry logic
        
        Args:
            func: Async function to wrap with retry logic
            
        Returns:
            Wrapped async function with retry capability
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self._execute_async_with_retry(func, *args, **kwargs)
        
        return wrapper
    
    def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute synchronous function with retry logic
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.config.initial_delay
        
        for attempt in range(self.config.max_retries + 1):
            self.retry_stats["total_attempts"] += 1
            
            try:
                result = func(*args, **kwargs)
                
                if attempt > 0:
                    self.retry_stats["successful_retries"] += 1
                    logger.info(f"✅ Operation succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(e):
                    logger.error(f"❌ Non-retryable exception: {type(e).__name__}")
                    self.retry_stats["failed_operations"] += 1
                    raise
                
                if attempt < self.config.max_retries:
                    self.retry_stats["total_retries"] += 1
                    logger.warning(f"⚠️  Attempt {attempt + 1}/{self.config.max_retries + 1} failed: {str(e)}")
                    logger.info(f"🔄 Retrying in {delay:.1f}s...")
                    
                    time.sleep(delay)
                    delay = min(delay * self.config.backoff_factor, self.config.max_delay)
                else:
                    self.retry_stats["failed_operations"] += 1
                    logger.error(f"❌ All {self.config.max_retries + 1} attempts failed")
        
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All retry attempts exhausted without capturing an exception")
    
    async def _execute_async_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute asynchronous function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        delay = self.config.initial_delay
        
        for attempt in range(self.config.max_retries + 1):
            self.retry_stats["total_attempts"] += 1
            
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 0:
                    self.retry_stats["successful_retries"] += 1
                    logger.info(f"✅ Async operation succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self._should_retry(e):
                    logger.error(f"❌ Non-retryable exception: {type(e).__name__}")
                    self.retry_stats["failed_operations"] += 1
                    raise
                
                if attempt < self.config.max_retries:
                    self.retry_stats["total_retries"] += 1
                    logger.warning(f"⚠️  Async attempt {attempt + 1}/{self.config.max_retries + 1} failed: {str(e)}")
                    logger.info(f"🔄 Retrying in {delay:.1f}s...")
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * self.config.backoff_factor, self.config.max_delay)
                else:
                    self.retry_stats["failed_operations"] += 1
                    logger.error(f"❌ All {self.config.max_retries + 1} async attempts failed")
        
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All async retry attempts exhausted without capturing an exception")
    
    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if an exception should trigger a retry
        
        Args:
            exception: The caught exception
            
        Returns:
            True if should retry, False otherwise
        """
        for exc_type in self.config.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        return False
    
    def get_stats(self) -> dict:
        """
        Get retry statistics
        
        Returns:
            Dictionary with retry statistics
        """
        return {
            **self.retry_stats,
            "success_rate": (
                (self.retry_stats["total_attempts"] - self.retry_stats["failed_operations"]) 
                / max(self.retry_stats["total_attempts"], 1) * 100
            ),
            "config": {
                "max_retries": self.config.max_retries,
                "initial_delay": self.config.initial_delay,
                "max_delay": self.config.max_delay,
                "backoff_factor": self.config.backoff_factor
            }
        }
    
    def reset_stats(self):
        """Reset retry statistics"""
        self.retry_stats = {
            "total_attempts": 0,
            "total_retries": 0,
            "successful_retries": 0,
            "failed_operations": 0
        }
        logger.info("📊 Retry statistics reset")


def create_retry_mechanism(max_retries: int = 3, 
                          initial_delay: float = 1.0,
                          backoff_factor: float = 2.0) -> RetryMechanism:
    """
    Factory function to create a retry mechanism with custom settings
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff
        
    Returns:
        Configured RetryMechanism instance
    """
    config = RetryConfig(
        max_retries=max_retries,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor
    )
    return RetryMechanism(config)
