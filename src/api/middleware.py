"""
API middleware for authentication and rate limiting.
"""

from time import time
from typing import Callable, Dict

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit for request."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Clean up old entries (older than 1 minute)
        current_time = time()
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip] if current_time - t < 60
            ]

        # Check rate limit
        if client_ip in self.request_counts:
            if len(self.request_counts[client_ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                )

        # Record request
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        self.request_counts[client_ip].append(current_time)

        # Process request
        response = await call_next(request)
        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Basic API key authentication middleware."""

    def __init__(self, app, api_keys: list = None):
        super().__init__(app)
        self.api_keys = api_keys or []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check API key for protected endpoints."""
        # Skip authentication for health and docs endpoints
        if request.url.path in ["/api/v1/health", "/docs", "/redoc", "/openapi.json", "/"]:
            return await call_next(request)

        # Check for API key in header
        api_key = request.headers.get("X-API-Key")

        # If no API keys configured, allow all requests
        if not self.api_keys:
            return await call_next(request)

        # If API keys are configured, require authentication
        if not api_key or api_key not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide X-API-Key header.",
            )

        return await call_next(request)
