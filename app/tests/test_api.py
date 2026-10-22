import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from flask import Flask

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
