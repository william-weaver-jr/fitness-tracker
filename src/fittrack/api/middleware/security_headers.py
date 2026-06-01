"""Security headers middleware."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "strict-origin-when-cross-origin",
    "x-xss-protection": "0",  # Modern browsers ignore it; CSP is the replacement
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:
        next_fn = call_next  # type: ignore[assignment]
        response: Response = await next_fn(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
