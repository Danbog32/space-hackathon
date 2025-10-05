"""Audit logging middleware."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create logs directory if it doesn't exist
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# File handler for audit logs
audit_handler = logging.FileHandler(LOG_DIR / "audit.log")
audit_handler.setFormatter(
    logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
    )
)
audit_logger.addHandler(audit_handler)

# Console handler for development
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - AUDIT - %(message)s")
)
audit_logger.addHandler(console_handler)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs all write operations (POST, PUT, PATCH, DELETE) for security auditing.
    
    Logs include:
    - Timestamp
    - User (from JWT if available)
    - IP address
    - HTTP method and path
    - Request body (sanitized)
    - Response status
    """
    
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    SENSITIVE_FIELDS = {"password", "token", "secret", "api_key"}
    
    async def dispatch(self, request: Request, call_next):
        # Only log write operations
        if request.method not in self.WRITE_METHODS:
            return await call_next(request)
        
        # Extract user info
        user_id = self._extract_user_from_request(request)
        ip_address = request.client.host if request.client else "unknown"
        
        # Get request body (if JSON)
        body = await self._get_request_body(request)
        
        # Process request
        response = await call_next(request)
        
        # Log the operation
        log_entry = {
            "user_id": user_id or "anonymous",
            "ip": ip_address,
            "method": request.method,
            "path": str(request.url.path),
            "query": str(request.url.query) if request.url.query else None,
            "body": self._sanitize_body(body),
            "status": response.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        audit_logger.info(json.dumps(log_entry))
        
        return response
    
    def _extract_user_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token if present."""
        try:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # Token present - in production, decode and extract user_id
                # For now, just log that auth was present
                return "authenticated_user"
            return None
        except Exception:
            return None
    
    async def _get_request_body(self, request: Request) -> Optional[dict]:
        """Safely extract request body."""
        try:
            if request.headers.get("content-type") == "application/json":
                body = await request.json()
                return body
        except Exception:
            pass
        return None
    
    def _sanitize_body(self, body: Optional[dict]) -> Optional[dict]:
        """Remove sensitive fields from body before logging."""
        if not body:
            return None
        
        sanitized = body.copy()
        for field in self.SENSITIVE_FIELDS:
            if field in sanitized:
                sanitized[field] = "***REDACTED***"
        
        return sanitized


def log_security_event(
    event_type: str,
    user_id: Optional[str],
    details: dict,
    severity: str = "INFO"
):
    """
    Manually log a security event.
    
    Usage:
        log_security_event(
            "failed_login",
            user_id="user@example.com",
            details={"reason": "invalid_password", "attempts": 3},
            severity="WARNING"
        )
    """
    log_entry = {
        "event_type": event_type,
        "user_id": user_id or "anonymous",
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    log_method = getattr(audit_logger, severity.lower(), audit_logger.info)
    log_method(json.dumps(log_entry))

