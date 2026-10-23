"""Prometheus request metrics for the Atlas Flask application."""

from time import perf_counter

from flask import Response, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

_ALLOWED_METHODS = frozenset(
    {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
)
_METRICS_ENDPOINT = "atlas_metrics"


def _method_label(method):
    if method in _ALLOWED_METHODS:
        return method
    return "OTHER"


def init_metrics(app):
    """Register per-application metrics, hooks, and the scrape endpoint."""
    existing_metrics = app.extensions.get("atlas_metrics")
    if existing_metrics is not None:
        return existing_metrics

    registry = CollectorRegistry()
    request_counter = Counter(
        "atlas_http_requests_total",
        "Total HTTP requests handled by the Atlas API.",
        labelnames=("method", "route", "status"),
        registry=registry,
    )
    request_duration = Histogram(
        "atlas_http_request_duration_seconds",
        "HTTP request latency in seconds.",
        labelnames=("method", "route", "status"),
        registry=registry,
    )

    metrics = {
        "registry": registry,
        "request_counter": request_counter,
        "request_duration": request_duration,
    }
    app.extensions["atlas_metrics"] = metrics

    @app.before_request
    def _start_request_timer():
        if request.endpoint != _METRICS_ENDPOINT:
            g.atlas_metrics_started_at = perf_counter()

    @app.after_request
    def _record_request_metrics(response):
        if request.endpoint == _METRICS_ENDPOINT:
            return response

        started_at = getattr(g, "atlas_metrics_started_at", None)
        if started_at is None:
            return response

        route = request.url_rule.rule if request.url_rule is not None else "unmatched"
        labels = {
            "method": _method_label(request.method),
            "route": route,
            "status": str(response.status_code),
        }
        elapsed_seconds = perf_counter() - started_at

        request_counter.labels(**labels).inc()
        request_duration.labels(**labels).observe(elapsed_seconds)
        return response

    def _metrics_response():
        return Response(
            generate_latest(registry),
            content_type=CONTENT_TYPE_LATEST,
        )

    app.add_url_rule(
        "/metrics",
        endpoint=_METRICS_ENDPOINT,
        view_func=_metrics_response,
        methods=["GET"],
    )

    return metrics
