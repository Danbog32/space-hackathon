"""Security middleware for FastAPI application."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables XSS filter in browsers
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    - Content-Security-Policy: Prevents XSS and other attacks (basic)
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Basic CSP - adjust based on your needs
        # Allow inline styles for demo purposes, tighten in production
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )
        
        # Server header removal (hide implementation details)
        if "Server" in response.headers:
            del response.headers["Server"]
        
        return response


class RequestSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitizes incoming requests to prevent injection attacks.
    Validates common attack patterns in query parameters and headers.
    """
    
    BLOCKED_PATTERNS = [
        "<script",
        "javascript:",
        "onerror=",
        "onload=",
        "../",
        "..\\",
        "DROP TABLE",
        "INSERT INTO",
        "DELETE FROM",
        "UNION SELECT",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check query parameters
        query_string = str(request.url.query).lower()
        for pattern in self.BLOCKED_PATTERNS:
            if pattern.lower() in query_string:
                return Response(
                    content=f"Malicious pattern detected: {pattern}",
                    status_code=400,
                )
        
        # Check user agent for obvious bots/scrapers (optional)
        user_agent = request.headers.get("user-agent", "").lower()
        suspicious_agents = ["sqlmap", "nmap", "nikto", "masscan"]
        if any(agent in user_agent for agent in suspicious_agents):
            return Response(
                content="Access denied",
                status_code=403,
            )
        
        return await call_next(request)

