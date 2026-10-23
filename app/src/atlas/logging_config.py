"""Structured request logging for the Atlas Flask application."""

import json
import logging
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from flask import g, request
from werkzeug.exceptions import HTTPException, InternalServerError

_ALLOWED_METHODS = frozenset(
    {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
)
_UNMATCHED_ROUTE = "unmatched"
_HANDLER_MARKER = "_atlas_json_handler"


class JSONFormatter(logging.Formatter):
    """Format log records as compact JSON without exception messages."""

    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created, timezone.utc)
        payload = {
            "timestamp": timestamp.isoformat(timespec="milliseconds").replace(
                "+00:00", "Z"
            ),
            "level": record.levelname,
            "event": getattr(record, "atlas_event", "application.log"),
        }
        payload.update(getattr(record, "atlas_fields", {}))

        if record.exc_info and "error_type" not in payload:
            exception_type = record.exc_info[0]
            if exception_type is not None:
                payload["error_type"] = exception_type.__name__

        return json.dumps(payload, separators=(",", ":"))


def configure_logging():
    """Configure one JSON stream handler for the Atlas application logger."""
    logger = logging.getLogger("atlas")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    marked_handlers = [
        handler
        for handler in logger.handlers
        if getattr(handler, _HANDLER_MARKER, False)
    ]
    if marked_handlers:
        handler, *duplicates = marked_handlers
        for duplicate in duplicates:
            logger.removeHandler(duplicate)
            duplicate.close()
        handler.setFormatter(JSONFormatter())
    else:
        handler = logging.StreamHandler()
        setattr(handler, _HANDLER_MARKER, True)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


def _method_label(method):
    if method in _ALLOWED_METHODS:
        return method
    return "OTHER"


def init_request_logging(app):
    """Register request IDs, safe error handling, and completion events."""
    if app.extensions.get("atlas_request_logging"):
        return

    logger = logging.getLogger(app.name)
    app.extensions["atlas_request_logging"] = True

    @app.before_request
    def _start_request_logging():
        g.atlas_request_id = uuid4().hex
        g.atlas_request_started_at = perf_counter()

    @app.errorhandler(Exception)
    def _handle_unexpected_exception(error):
        if isinstance(error, HTTPException):
            return error
        if app.debug:
            raise error

        g.atlas_error_type = type(error).__name__
        return InternalServerError()

    @app.after_request
    def _log_request_completion(response):
        request_id = getattr(g, "atlas_request_id", None)
        if request_id is None:
            request_id = uuid4().hex
            g.atlas_request_id = request_id

        response.headers["X-Request-ID"] = request_id

        route = (
            request.url_rule.rule
            if request.url_rule is not None
            else _UNMATCHED_ROUTE
        )
        status_code = response.status_code
        if status_code < 400 and route in {"/health", "/metrics"}:
            return response

        started_at = getattr(g, "atlas_request_started_at", None)
        duration_ms = 0.0 if started_at is None else (perf_counter() - started_at) * 1000
        fields = {
            "request_id": request_id,
            "method": _method_label(request.method),
            "route": route,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 3),
        }
        error_type = getattr(g, "atlas_error_type", None)
        if error_type is not None:
            fields["error_type"] = error_type

        level = logging.ERROR if status_code >= 500 else logging.INFO
        logger.log(
            level,
            "http.request.completed",
            extra={
                "atlas_event": "http.request.completed",
                "atlas_fields": fields,
            },
        )
        return response
