# 🔒 Security Architecture

## Overview
This document describes the security measures implemented in the Astro-Zoom application for the NASA "Embiggen Your Eyes!" hackathon.

## Security Objectives

| Objective | Description | Status |
|-----------|-------------|--------|
| **Integrity** | Ensure annotations and datasets cannot be tampered with | ✅ Implemented |
| **Availability** | Maintain service responsiveness, prevent DoS | ✅ Implemented |
| **Confidentiality** | Protect sensitive metadata and tokens | ✅ Implemented |
| **Public Safety** | Limit guest users to read-only operations | ✅ Implemented |

## Threat Model

| Threat | Vector | Mitigation | Priority |
|--------|--------|------------|----------|
| Unauthorized writes | Direct API access | JWT auth + RBAC | High |
| CORS bypass/XSS | Malicious frontend | Strict CORS + CSP headers | High |
| DoS via search | Heavy AI operations | Per-IP rate limiting | Medium |
| Dependency vulnerabilities | Outdated libraries | Automated scanning | Medium |
| Logging exposure | Sensitive data in logs | Sanitized logging | Medium |
| SQL Injection | Malicious inputs | ORM + input validation | High |

## Security Features

### 1. Authentication & Authorization

#### JWT-Based Authentication
- **Algorithm**: HS256
- **Token Lifetime**: 1 hour (configurable via `JWT_EXPIRATION`)
- **Secret**: Stored in environment variable `JWT_SECRET`

**Roles:**
- `viewer` - Read-only access (GET requests)
- `editor` - Can create/update/delete annotations
- `admin` - Full access including dataset management

**Protected Endpoints:**
```
POST   /annotations     - Requires: editor
PUT    /annotations/:id - Requires: editor
DELETE /annotations/:id - Requires: editor
POST   /datasets/ingest - Requires: admin
```

#### Implementation
```python
# apps/api/app/auth.py
from app.middleware.auth import require_auth

@router.post("/annotations")
@require_auth(role="editor")
async def create_annotation(...):
    pass
```

### 2. CORS Configuration

**Allowed Origins:**
- `http://localhost:3000` (Development)
- `http://localhost:8000` (API docs)
- Production domains (configured via `CORS_ORIGINS`)

**Configuration:**
```python
# apps/api/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # From .env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Security Headers

All responses include the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable XSS filter |
| `Referrer-Policy` | `no-referrer` | Control referrer information |
| `Permissions-Policy` | `geolocation=()` | Disable unnecessary features |
| `Content-Security-Policy` | See below | Prevent XSS attacks |

**Content Security Policy:**
```
default-src 'self';
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
```

### 4. Rate Limiting

**Implemented Using:** `slowapi` (based on Flask-Limiter)

**Limits:**
- `/search` endpoint: 10 requests/minute/IP
- `/annotations` endpoints: 20 requests/minute/IP
- Global default: 30 requests/minute/IP

**Response:**
- HTTP 429 Too Many Requests
- `Retry-After` header included

**Configuration:**
```python
# apps/api/app/routers/search.py
from slowapi import Limiter

@router.get("/")
@limiter.limit("10/minute")
async def search(...):
    pass
```

### 5. Audit Logging

**What's Logged:**
- All write operations (POST, PUT, PATCH, DELETE)
- Timestamp (UTC)
- User ID (from JWT)
- IP address
- HTTP method and path
- Request body (sanitized)
- Response status code

**Log Format:**
```json
{
  "timestamp": "2025-10-04T12:34:56.789Z",
  "user_id": "user@example.com",
  "ip": "192.168.1.100",
  "method": "POST",
  "path": "/annotations",
  "query": null,
  "body": {"label": "Crater", "geometry": {...}},
  "status": 201
}
```

**Log Location:**
- File: `/app/logs/audit.log`
- Console: Development only

**View Logs:**
```bash
# View last 50 entries
make audit

# View live logs
tail -f logs/audit.log | jq
```

**Security Events:**
```python
from app.middleware.audit import log_security_event

log_security_event(
    "failed_login",
    user_id="user@example.com",
    details={"reason": "invalid_password", "attempts": 3},
    severity="WARNING"
)
```

### 6. Request Sanitization

**Blocked Patterns:**
- XSS attempts: `<script>`, `javascript:`, `onerror=`
- Path traversal: `../`, `..\\`
- SQL injection: `DROP TABLE`, `UNION SELECT`, etc.

**Suspicious User Agents:**
- `sqlmap`, `nmap`, `nikto`, `masscan`

**Response:** HTTP 400 Bad Request or 403 Forbidden

### 7. Dependency Security

**Automated Scanning:**
```bash
# Python dependencies
make security

# Or manually:
cd apps/api && pip-audit
cd apps/ai && pip-audit
cd apps/web && pnpm audit
```

**Docker Build Integration:**
```dockerfile
# infra/Dockerfile.api
RUN pip install pip-audit && \
    pip-audit --desc || true
```

**Update Policy:**
- Check weekly
- Patch critical vulnerabilities within 24h
- Update minor/moderate vulnerabilities during sprints

### 8. Docker Security

**Best Practices:**
- ✅ Non-root user in containers
- ✅ Minimal base images (`python:3.11-slim`)
- ✅ Multi-stage builds
- ✅ No secrets in images
- ✅ Health checks
- ✅ Resource limits

**Non-Root User:**
```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

## Environment Variables

**Security-Critical Variables:**
```bash
JWT_SECRET=<strong-random-string>  # REQUIRED
CORS_ORIGINS=<allowed-origins>     # REQUIRED
DATABASE_URL=<connection-string>   # REQUIRED
```

**Never commit:**
- `.env` files with real secrets
- `JWT_SECRET` values
- Database credentials
- API keys

**Use:**
- `.env.example` for templates
- `.env.development` for local dev
- Secret management tools for production (AWS Secrets Manager, Vault, etc.)

## Deployment Security

### Development
```bash
# Use development environment
cp .env.development .env
make dev
```

### Production Checklist

- [ ] Change `JWT_SECRET` to strong random value (32+ chars)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Update `CORS_ORIGINS` to production domains only
- [ ] Set `DEBUG=false`
- [ ] Configure firewall rules
- [ ] Set up monitoring/alerting
- [ ] Enable backup strategy
- [ ] Review rate limits
- [ ] Enable audit log rotation
- [ ] Use secrets management tool
- [ ] Scan Docker images
- [ ] Set up WAF (if using cloud)

## Security Testing

### Manual Testing
```bash
# Test rate limiting
for i in {1..15}; do curl http://localhost:8000/search?q=test; done

# Test CORS
curl -H "Origin: http://evil.com" http://localhost:8000/datasets

# Test auth
curl -X POST http://localhost:8000/annotations \
  -H "Content-Type: application/json" \
  -d '{"label": "test"}'

# Test security headers
curl -I http://localhost:8000/health
```

### Automated Testing
```bash
# Run security tests
make test-security

# Scan dependencies
make security
```

## Incident Response

### In Case of Security Issue:

1. **Immediate Actions:**
   - Stop affected services if critical
   - Review audit logs: `make audit`
   - Check for unauthorized access
   - Document the incident

2. **Investigation:**
   - Analyze logs in `/app/logs/audit.log`
   - Check Docker logs: `make logs`
   - Review recent changes in Git

3. **Remediation:**
   - Apply security patches
   - Rotate compromised secrets
   - Update firewall rules
   - Notify affected users (if any)

4. **Post-Mortem:**
   - Document root cause
   - Update security measures
   - Add detection/prevention mechanisms

## Security Contacts

**Hackathon Team:**
- Security Lead: Illia
- Backend Lead: Edward
- Infrastructure: Ivan

**Report Security Issues:**
Create a private GitHub issue or contact team lead directly.

## Compliance

**Demo Environment:**
- Read-only data (public NASA imagery)
- No PII collected
- Educational use only

**Production Considerations:**
- GDPR compliance (if EU users)
- Data retention policies
- Privacy policy
- Terms of service

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)

---

**Last Updated:** 2025-10-04  
**Version:** 0.1.0  
**Status:** Active Development

