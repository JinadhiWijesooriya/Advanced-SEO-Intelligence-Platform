"""
Request / Response Logging Middleware — Phase 10

Logs every HTTP request with:
  - Unique X-Request-ID header (UUID4, attached to both request and response)
  - HTTP method, path, query string
  - Response status code
  - Duration in milliseconds

The X-Request-ID is propagated back to the client so frontend errors can be
correlated with backend log lines.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that logs every HTTP request/response cycle
    and attaches a unique X-Request-ID header.
    """

    # Paths to skip (health-checks, metrics — avoids log noise)
    SKIP_PATHS = {"/", "/api/v1/health", "/api/health", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        path = request.url.path
        skip = path in self.SKIP_PATHS or path.startswith("/static")

        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # Always attach the request ID to the response
        response.headers["X-Request-ID"] = request_id

        if not skip:
            status = response.status_code
            method = request.method
            log_level = logging.WARNING if status >= 400 else logging.INFO

            logger.log(
                log_level,
                f"{method} {path} → {status} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status,
                    "duration_ms": duration_ms,
                },
            )

        return response
