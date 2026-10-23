import json
import os
import subprocess
import sys
import tomllib
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


def get_json(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert response.mimetype == "application/json"

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


def test_unsupported_methods_use_bounded_other_label(app):
    app.add_url_rule(
        "/custom-method",
        endpoint="custom_method",
        view_func=lambda: "ok",
        methods=["PURGE"],
    )
    client = app.test_client()

    response = client.open("/custom-method", method="PURGE")

    assert response.status_code == 200
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
