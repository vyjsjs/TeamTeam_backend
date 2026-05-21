"""Structured JSON logging middleware for request/response tracking."""

import time
import uuid
import json
import logging
import sys
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.metrics import http_errors_total

# Configure structured logger
logger = logging.getLogger("teamteam")
logger.setLevel(logging.INFO)

# JSON formatter
handler = logging.StreamHandler(sys.stdout)


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Merge extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data, ensure_ascii=False)


handler.setFormatter(JSONFormatter())
logger.addHandler(handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request in JSON format.

    Captures: request_id, method, path, status_code, latency, user_id (if available).
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Attach request_id for downstream access
        request.state.request_id = request_id

        response: Response = await call_next(request)

        latency_ms = round((time.time() - start_time) * 1000, 2)

        user_id = getattr(request.state, "user_id", None)

        extra = {
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "client_ip": request.client.host if request.client else None,
        }
        if user_id is not None:
            extra["user_id"] = user_id

        # Determine log level by status code
        if response.status_code >= 500:
            level = logging.ERROR
            http_errors_total.labels(
                endpoint=str(request.url.path),
                status_code=str(response.status_code),
                error_type="server_error",
            ).inc()
        elif response.status_code >= 400:
            level = logging.WARNING
            http_errors_total.labels(
                endpoint=str(request.url.path),
                status_code=str(response.status_code),
                error_type="client_error",
            ).inc()
        else:
            level = logging.INFO

        record = logger.makeRecord(
            name="teamteam",
            level=level,
            fn="",
            lno=0,
            msg=f"{request.method} {request.url.path} → {response.status_code}",
            args=(),
            exc_info=None,
        )
        record.extra_data = extra
        logger.handle(record)

        # Add request-id to response headers for tracing
        response.headers["X-Request-ID"] = request_id
        return response
