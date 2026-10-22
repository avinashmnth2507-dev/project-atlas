# Project Atlas API

This directory contains the Flask API foundation for Project Atlas. Local development and tests run on your machine; they do not create AWS resources, start a database, or require Docker. Python package installation uses the configured package index.

## Prerequisites

- Python 3.14 or newer. The project is configured for Python 3.14; Python 3.14.8 was used for the ATLAS-002 local checks.
- `pip`, included with Python.

## Create a local environment

Run these commands from `app/`:

```bash
python3 -m venv .venv-atlas002
source .venv-atlas002/bin/activate
python -m pip install -r requirements-dev.txt
```

The `requirements-dev.txt` file includes the runtime requirements and pytest. The environment directory is ignored by Git. The older `.venv/` may reference a Python installation that is no longer present; leave it untouched and use the separate environment above.

## Start the API

With the environment active and the current directory set to `app/`:

```bash
PYTHONPATH=src python run.py
```

The development server listens on port 5000. Visit `http://127.0.0.1:5000/`. To use production configuration for a local check, set `FLASK_ENV` before startup:

```bash
FLASK_ENV=production PYTHONPATH=src python run.py
```

The app defaults to the `development` environment. `DEBUG` is enabled only for `development` and disabled for `production`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Welcome response and running status. |
| GET | `/health` | Health status, application name, and version. |
| GET | `/info` | Application name, version, and configured environment. |
| GET | `/version` | Application version. |

All endpoints return JSON. The version is `0.1.0`, sourced from the package version in `pyproject.toml` through the application configuration.

## Run tests and compilation checks

From `app/`, with the environment active:

```bash
python -m pytest
python -m compileall -q src run.py
```

The pytest suite uses Flask's test client and does not start a web server. It covers endpoint responses, JSON content, package-version consistency, the application factory, and development/production debug settings.

## Troubleshooting

- **`ModuleNotFoundError: atlas`:** run commands from `app/` and set `PYTHONPATH=src` for direct startup. Pytest reads this source path from `pyproject.toml`.
- **`ModuleNotFoundError: flask` or `pytest`:** activate `.venv-atlas002` and run `python -m pip install -r requirements-dev.txt`.
- **The old `.venv/bin/python` cannot start:** it was created from a Python installation that is no longer available. This guide uses a separate environment so the existing directory is preserved.
- **Port 5000 is busy:** stop the other local development server before starting this one.

No cloud credentials or paid services are needed for the backend workflow.

## Build and run the local Docker image

From the repository root, build the commit-specific local image and start only the Atlas API:

```bash
docker compose -f compose.yaml build api
docker compose -f compose.yaml up --detach api
docker compose -f compose.yaml ps
```

The image tag is `project-atlas-api:0.1.0-atlas003-6461902`. Compose binds `127.0.0.1:5055` on the host to port `5000` in the container. The image uses the official Python 3.14.8 slim Bookworm base pinned to its image digest, installs only production requirements, and copies the application into `/opt/atlas`. It starts Gunicorn with one synchronous worker, disables Gunicorn's optional control socket, runs as UID/GID `10001`, and has a Python standard-library health check for `/health`.

The Compose service limits the container to one CPU and 256 MiB, makes the root filesystem read-only, drops Linux capabilities, disables privilege escalation, and provides a small writable `/tmp`. Its logs are size-limited. No registry, cloud service, database, or other container is required.

Flask's built-in server (`python run.py`) is for local development. The container uses Gunicorn, a production WSGI server, to serve the same Flask application factory.

### Check routes and logs

```bash
curl --fail http://127.0.0.1:5055/
curl --fail http://127.0.0.1:5055/health
curl --fail http://127.0.0.1:5055/info
curl --fail http://127.0.0.1:5055/version
docker compose -f compose.yaml logs --follow api
```

The test suite remains a separate host-side check:

```bash
cd app
.venv-atlas002/bin/python -m pytest -q
```

### Stop and clean up Atlas resources

Stop and remove only the container and network created by this Compose project:

```bash
docker compose -f compose.yaml down
```

If you also want to remove the Atlas image, remove only its exact tag:

```bash
docker image rm project-atlas-api:0.1.0-atlas003-6461902
```

Do not use broad prune commands for this project; they can remove images, containers, or volumes belonging to other projects. The Compose file creates no named volumes.
