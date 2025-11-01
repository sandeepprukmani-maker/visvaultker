import time
from collections import defaultdict
from typing import Dict
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > minute_ago
        ]
        
        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False
        
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        now = time.time()
        minute_ago = now - 60
        
        recent_requests = [
            req_time for req_time in self.requests.get(identifier, [])
            if req_time > minute_ago
        ]
        
        return max(0, self.requests_per_minute - len(recent_requests))

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        if not self.limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(self.limiter.get_remaining(client_ip))
        return response
