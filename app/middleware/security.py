"""
Security Middleware
Authentication, rate limiting, and security utilities
"""
import os
import time
import logging
from functools import wraps
from flask import request, jsonify
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed for client
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        requests = self.requests[client_id]
        requests = [req_time for req_time in requests if now - req_time < self.window_seconds]
        
        if len(requests) >= self.max_requests:
            oldest_request = min(requests)
            retry_after = int(self.window_seconds - (now - oldest_request)) + 1
            return False, retry_after
        
        requests.append(now)
        self.requests[client_id] = requests
        
        self._cleanup_old_entries(now)
        
        return True, None
    
    def _cleanup_old_entries(self, now: float):
        """Clean up old entries to prevent memory bloat"""
        clients_to_remove = []
        for client_id, requests in self.requests.items():
            active_requests = [req_time for req_time in requests if now - req_time < self.window_seconds]
            if not active_requests:
                clients_to_remove.append(client_id)
            else:
                self.requests[client_id] = active_requests
        
        for client_id in clients_to_remove:
            del self.requests[client_id]


rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def require_api_key(f):
    """
    Decorator to require API key authentication
    
    Checks for API key in:
    1. X-API-Key header
    2. api_key query parameter
    
    Set API_KEY environment variable to enable authentication.
    If API_KEY is not set, authentication is disabled (development mode).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_api_key = os.environ.get('API_KEY')
        
        if not expected_api_key:
            logger.warning("⚠️  API_KEY not set - authentication disabled (development mode)")
            return f(*args, **kwargs)
        
        provided_api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not provided_api_key:
            logger.warning(f"🔒 Unauthorized request from {request.remote_addr} - no API key provided")
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please provide an API key via X-API-Key header or api_key parameter'
            }), 401
        
        if provided_api_key != expected_api_key:
            logger.warning(f"🔒 Unauthorized request from {request.remote_addr} - invalid API key")
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(f):
    """
    Decorator to apply rate limiting
    
    Uses IP address as client identifier
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_id = request.remote_addr or 'unknown'
        
        allowed, retry_after = rate_limiter.is_allowed(client_id)
        
        if not allowed:
            logger.warning(f"⚠️  Rate limit exceeded for {client_id}")
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Please try again in {retry_after} seconds.',
                'retry_after': retry_after
            }), 429
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_engine_type(engine_type: str) -> Tuple[bool, Optional[str]]:
    """
    Validate engine type parameter
    
    Args:
        engine_type: Engine type to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_engines = ['browser_use']
    
    if engine_type not in valid_engines:
        return False, f"Invalid engine type '{engine_type}'. Must be: browser_use"
    
    return True, None


def validate_instruction(instruction: str) -> Tuple[bool, Optional[str]]:
    """
    Validate instruction parameter
    
    Args:
        instruction: Instruction to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not instruction or not instruction.strip():
        return False, "Instruction cannot be empty"
    
    if len(instruction) > 5000:
        return False, "Instruction is too long (maximum 5000 characters)"
    
    return True, None


def sanitize_error_message(error: Exception) -> str:
    """
    Convert internal exception to user-safe error message
    
    Args:
        error: Exception to sanitize
        
    Returns:
        User-safe error message
    """
    error_str = str(error).lower()
    
    if 'openai' in error_str or 'api' in error_str:
        return "AI service error. Please try again later."
    
    if 'browser' in error_str or 'playwright' in error_str:
        return "Browser automation error. Please try again."
    
    if 'timeout' in error_str:
        return "Operation timed out. The task took too long to complete."
    
    if 'permission' in error_str or 'denied' in error_str:
        return "Permission denied. Please check your access rights."
    
    return "An unexpected error occurred. Please try again."
