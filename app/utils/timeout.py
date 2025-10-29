"""
Cross-platform timeout utility
Works on Windows, Linux, and macOS with proper cancellation
"""
import threading
import logging
from typing import Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when operation times out"""
    pass


def run_with_timeout(func: Callable, timeout_seconds: int, *args, **kwargs) -> Any:
    """
    Run a function with a timeout (cross-platform)
    
    Note: This implementation returns promptly on timeout but cannot
    forcefully terminate the underlying function if it's stuck. The
    worker thread continues in the background but HTTP request returns.
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result from func
        
    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, *args, **kwargs)
    
    try:
        result = future.result(timeout=timeout_seconds)
        executor.shutdown(wait=False)
        return result
    except FutureTimeoutError:
        logger.warning(f"⏱️ Operation timed out after {timeout_seconds} seconds")
        future.cancel()
        executor.shutdown(wait=False)
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    except Exception as e:
        logger.error(f"❌ Error during timed execution: {str(e)}")
        executor.shutdown(wait=False)
        raise
