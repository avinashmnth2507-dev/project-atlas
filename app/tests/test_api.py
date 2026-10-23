import io
import json
import logging
import os
import re
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import pytest
from flask import Flask
from prometheus_client import CONTENT_TYPE_LATEST

from atlas import create_app
from atlas.config import Config

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_METADATA = tomllib.loads((APP_DIR / "pyproject.toml").read_text())
PROJECT_VERSION = PROJECT_METADATA["project"]["version"]
CONFIG_PROBE = """
import json
from atlas import create_app

app = create_app()
print(json.dumps({
    "environment": app.config["ENVIRONMENT"],
    "debug": app.config["DEBUG"],
}))
"""


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def log_output(app):
    logger = logging.getLogger(app.name)
    handler = next(
        handler
        for handler in logger.handlers
        if getattr(handler, "_atlas_json_handler", False)
    )
    original_stream = handler.stream
    stream = io.StringIO()
    handler.setStream(stream)
    try:
        yield stream
    finally:
        handler.setStream(original_stream)


def parse_log_output(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines()]


def get_json(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])

    return response.get_json()


def test_application_factory_creates_a_usable_flask_app(app):
    assert isinstance(app, Flask)
    assert app.test_client().get("/health").status_code == 200


def test_home_endpoint_returns_expected_response(client):
    assert get_json(client, "/") == {
        "message": "Welcome to Project Atlas!",
        "application": "Project Atlas",
        "status": "running",
    }


def test_health_endpoint_returns_healthy_status(client):
    body = get_json(client, "/health")

    assert body["status"] == "healthy"
    assert body["application"] == "Project Atlas"
    assert body["version"] == PROJECT_VERSION


def test_info_endpoint_returns_application_metadata(client):
    assert get_json(client, "/info") == {
        "application": "Project Atlas",
        "version": PROJECT_VERSION,
        "environment": Config.ENVIRONMENT,
    }


def test_version_endpoint_returns_package_version(client):
    assert get_json(client, "/version") == {"version": PROJECT_VERSION}


def test_version_bearing_endpoints_match_package_version(client):
    versions = {
        path: get_json(client, path)["version"]
        for path in ("/health", "/info", "/version")
    }

    assert set(versions.values()) == {PROJECT_VERSION}


def test_metrics_endpoint_returns_prometheus_exposition(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])
    assert response.mimetype == "text/plain"
    assert response.content_type == CONTENT_TYPE_LATEST
    exposition = response.get_data(as_text=True)
    assert "# TYPE atlas_http_requests_total counter" in exposition
    assert "# TYPE atlas_http_request_duration_seconds histogram" in exposition


def test_request_metrics_include_counter_and_histogram_samples(app, client):
    response = client.get("/info")
    assert response.status_code == 200

    registry = app.extensions["atlas_metrics"]["registry"]
    labels = {"method": "GET", "route": "/info", "status": "200"}

    assert registry.get_sample_value("atlas_http_requests_total", labels) == 1
    assert (
        registry.get_sample_value(
            "atlas_http_request_duration_seconds_count", labels
        )
        == 1
    )
    assert (
        registry.get_sample_value(
            "atlas_http_request_duration_seconds_bucket",
            {**labels, "le": "+Inf"},
        )
        == 1
    )
    assert (
        registry.get_sample_value("atlas_http_request_duration_seconds_sum", labels)
        >= 0
    )

    exposition = client.get("/metrics").get_data(as_text=True)
    assert "atlas_http_request_duration_seconds_bucket{" in exposition
    assert "atlas_http_request_duration_seconds_count{" in exposition
    assert "atlas_http_request_duration_seconds_sum{" in exposition
    assert "request_id=" not in exposition


def test_unmatched_routes_do_not_expose_raw_url_or_query_labels(client, app):
    raw_path = "/missing-user-7913"
    sensitive_query = "token=sentinel-value-5ab93&email=private@example.test"

    response = client.get(f"{raw_path}?{sensitive_query}")

    assert response.status_code == 404
    registry = app.extensions["atlas_metrics"]["registry"]
    labels = {"method": "GET", "route": "unmatched", "status": "404"}
    assert registry.get_sample_value("atlas_http_requests_total", labels) == 1

    exposition = client.get("/metrics").get_data(as_text=True)
    assert 'route="unmatched"' in exposition
    assert raw_path not in exposition
    assert sensitive_query not in exposition
    assert "sentinel-value-5ab93" not in exposition
    assert "private@example.test" not in exposition


def test_dynamic_routes_use_the_matched_route_template(app):
    app.add_url_rule(
        "/records/<record_id>",
        endpoint="record",
        view_func=lambda record_id: record_id,
        methods=["GET"],
    )
    client = app.test_client()

    response = client.get("/records/private-record-42?token=private-query-value")

    assert response.status_code == 200
    registry = app.extensions["atlas_metrics"]["registry"]
    labels = {
        "method": "GET",
        "route": "/records/<record_id>",
        "status": "200",
    }
    assert registry.get_sample_value("atlas_http_requests_total", labels) == 1

    exposition = client.get("/metrics").get_data(as_text=True)
    assert 'route="/records/<record_id>"' in exposition
    assert "private-record-42" not in exposition
    assert "private-query-value" not in exposition


def test_unsupported_methods_use_bounded_other_label(app, log_output):
    app.add_url_rule(
        "/custom-method",
        endpoint="custom_method",
        view_func=lambda: "ok",
        methods=["PURGE"],
    )
    client = app.test_client()

    response = client.open("/custom-method", method="PURGE")

    assert response.status_code == 200
    assert parse_log_output(log_output)[0]["method"] == "OTHER"
    registry = app.extensions["atlas_metrics"]["registry"]
    labels = {"method": "OTHER", "route": "/custom-method", "status": "200"}
    assert registry.get_sample_value("atlas_http_requests_total", labels) == 1


def test_metrics_scrapes_do_not_count_themselves(client, app):
    registry = app.extensions["atlas_metrics"]["registry"]
    labels = {"method": "GET", "route": "/metrics", "status": "200"}

    first_response = client.get("/metrics")
    second_response = client.get("/metrics")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert registry.get_sample_value("atlas_http_requests_total", labels) is None


def test_flask_app_instances_have_independent_metric_registries():
    first_app = create_app()
    second_app = create_app()
    first_client = first_app.test_client()
    second_client = second_app.test_client()

    first_client.get("/health")

    first_registry = first_app.extensions["atlas_metrics"]["registry"]
    second_registry = second_app.extensions["atlas_metrics"]["registry"]
    first_labels = {"method": "GET", "route": "/health", "status": "200"}

    assert first_registry is not second_registry
    assert first_registry.get_sample_value("atlas_http_requests_total", first_labels)
    assert second_registry.get_sample_value("atlas_http_requests_total", first_labels) is None
    assert second_client.get("/metrics").status_code == 200


def test_request_logs_have_json_fields_utc_time_and_fresh_request_ids(
    client, log_output
):
    first_response = client.get("/info", headers={"X-Request-ID": "untrusted-id"})
    second_response = client.get("/info", headers={"X-Request-ID": "untrusted-id"})
    first_id = first_response.headers["X-Request-ID"]
    second_id = second_response.headers["X-Request-ID"]

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_id != "untrusted-id"
    assert second_id != "untrusted-id"
    assert first_id != second_id
    assert re.fullmatch(r"[0-9a-f]{32}", first_id)

    records = parse_log_output(log_output)
    assert len(records) == 2
    required_fields = {
        "timestamp",
        "level",
        "event",
        "request_id",
        "method",
        "route",
        "status_code",
        "duration_ms",
    }
    for record, request_id in zip(records, (first_id, second_id), strict=True):
        assert required_fields <= record.keys()
        assert record["level"] == "INFO"
        assert record["event"] == "http.request.completed"
        assert record["request_id"] == request_id
        assert record["method"] == "GET"
        assert record["route"] == "/info"
        assert record["status_code"] == 200
        assert isinstance(record["duration_ms"], (int, float))
        assert record["duration_ms"] >= 0
        assert record["timestamp"].endswith("Z")
        parsed_timestamp = datetime.fromisoformat(
            record["timestamp"].replace("Z", "+00:00")
        )
        assert parsed_timestamp.utcoffset().total_seconds() == 0


def test_logs_use_route_templates_and_never_log_sensitive_request_data(
    app, client, log_output
):
    app.add_url_rule(
        "/users/<user_id>",
        endpoint="private_user",
        view_func=lambda user_id: {"user_id": user_id},
        methods=["GET"],
    )
    private_path_value = "private-user-74391"
    private_query = "token=query-secret-921&email=private@example.test"
    private_authorization = "Bearer authorization-secret-732"
    private_cookie = "session=cookie-secret-184"

    response = client.get(
        f"/users/{private_path_value}?{private_query}",
        headers={
            "Authorization": private_authorization,
            "Cookie": private_cookie,
            "X-Request-ID": "incoming-request-id",
        },
    )

    assert response.status_code == 200
    records = parse_log_output(log_output)
    assert len(records) == 1
    assert records[0]["route"] == "/users/<user_id>"
    assert records[0]["request_id"] == response.headers["X-Request-ID"]
    output = log_output.getvalue()
    for sensitive_value in (
        private_path_value,
        private_query,
        "query-secret-921",
        "private@example.test",
        private_authorization,
        private_cookie,
        "incoming-request-id",
    ):
        assert sensitive_value not in output


def test_404_and_405_are_logged_without_raw_paths(client, log_output):
    not_found = client.get("/missing-private-path?token=private-query-token")
    method_not_allowed = client.post("/info")

    assert not_found.status_code == 404
    assert method_not_allowed.status_code == 405
    assert not_found.headers["X-Request-ID"]
    assert method_not_allowed.headers["X-Request-ID"]

    records = parse_log_output(log_output)
    assert [record["status_code"] for record in records] == [404, 405]
    assert all(record["level"] == "INFO" for record in records)
    assert records[0]["route"] == "unmatched"
    assert "/missing-private-path" not in log_output.getvalue()
    assert "private-query-token" not in log_output.getvalue()


def test_unexpected_production_errors_are_generic_and_logged_safely(
    app, client, log_output
):
    app.config["DEBUG"] = False

    def explode(value):
        raise RuntimeError(f"private exception detail {value}")

    app.add_url_rule(
        "/explode/<value>",
        endpoint="explode",
        view_func=explode,
        methods=["GET"],
    )

    response = client.get("/explode/private-path-secret?token=private-query-secret")

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    assert b"Internal Server Error" in response.get_data()
    assert b"private exception detail" not in response.get_data()
    assert b"private-path-secret" not in response.get_data()

    records = parse_log_output(log_output)
    assert len(records) == 1
    assert records[0]["level"] == "ERROR"
    assert records[0]["event"] == "http.request.completed"
    assert records[0]["request_id"] == response.headers["X-Request-ID"]
    assert records[0]["route"] == "/explode/<value>"
    assert records[0]["status_code"] == 500
    assert records[0]["error_type"] == "RuntimeError"
    for sensitive_value in (
        "private exception detail",
        "private-path-secret",
        "private-query-secret",
    ):
        assert sensitive_value not in log_output.getvalue()


def test_successful_health_and_metrics_requests_are_not_logged(app, client, log_output):
    health_response = client.get("/health")
    metrics_response = client.get("/metrics")

    assert health_response.status_code == 200
    assert metrics_response.status_code == 200
    assert health_response.headers["X-Request-ID"]
    assert metrics_response.headers["X-Request-ID"]
    assert log_output.getvalue() == ""

    registry = app.extensions["atlas_metrics"]["registry"]
    health_labels = {"method": "GET", "route": "/health", "status": "200"}
    assert registry.get_sample_value("atlas_http_requests_total", health_labels) == 1
    metrics_labels = {"method": "GET", "route": "/metrics", "status": "200"}
    assert registry.get_sample_value("atlas_http_requests_total", metrics_labels) is None


def test_repeated_app_creation_does_not_duplicate_handlers_or_request_events(
    app, client, log_output
):
    logger = logging.getLogger(app.name)
    second_app = create_app()
    second_client = second_app.test_client()

    marked_handlers = [
        handler
        for handler in logger.handlers
        if getattr(handler, "_atlas_json_handler", False)
    ]
    assert len(marked_handlers) == 1
    assert client.get("/info").status_code == 200
    assert second_client.get("/info").status_code == 200
    assert len(parse_log_output(log_output)) == 2


@pytest.mark.parametrize(
    ("environment", "expected_debug"),
    (("development", True), ("production", False)),
)
def test_debug_mode_matches_flask_environment(environment, expected_debug):
    process_environment = os.environ.copy()
    process_environment["FLASK_ENV"] = environment
    existing_pythonpath = process_environment.get("PYTHONPATH", "")
    process_environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(APP_DIR / "src"), existing_pythonpath))
    )

    result = subprocess.run(
        [sys.executable, "-c", CONFIG_PROBE],
        cwd=APP_DIR,
        env=process_environment,
        capture_output=True,
        check=True,
        text=True,
    )
    config = json.loads(result.stdout)

    assert config["environment"] == environment
    assert config["debug"] is expected_debug
