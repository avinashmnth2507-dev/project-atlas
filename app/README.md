# Project Atlas API

This directory contains the Flask API foundation for Project Atlas. Local development and tests run on your machine; they do not create AWS resources, start a database, or require Docker. Python package installation uses the configured package index.

## Prerequisites

- Python 3.14 or newer. The project and CI target Python 3.14.
- `pip`, included with Python.

## Create a local environment

Run these commands from `app/`:

```bash
python3 -m venv .venv-atlas002
source .venv-atlas002/bin/activate
python -m pip install -r requirements-dev.txt
```

The `requirements-dev.txt` file includes the runtime requirements, pytest, and the Ruff version used by CI. Virtual environments are ignored by Git and are not part of the application deliverable.

## Start the API

With the environment active and the current directory set to `app/`, start
the Flask CLI development server on loopback:

```bash
PYTHONPATH=src python -m flask --app atlas:create_app run --host 127.0.0.1 --port 5000
```

Visit `http://127.0.0.1:5000/`. To check the production application
configuration locally, set `FLASK_ENV` before startup:

```bash
FLASK_ENV=production PYTHONPATH=src python -m flask --app atlas:create_app run --host 127.0.0.1 --port 5000
```

The app defaults to the `development` environment. `DEBUG` is enabled only for
`development` and disabled for `production`. The Flask CLI still runs the
development server when `FLASK_ENV=production`; use Gunicorn for the container
runtime.

The separate `python run.py` entry point binds to `0.0.0.0:5000`. Direct
execution can expose the development server to other devices on the local
network, so use it only on a trusted network. The loopback-bound Flask CLI
command above is the safer local quick-start.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Welcome response and running status. |
| GET | `/health` | Health status, application name, and version. |
| GET | `/info` | Application name, version, and configured environment. |
| GET | `/version` | Application version. |
| GET | `/metrics` | Prometheus-compatible HTTP request metrics. |

The four application API endpoints return JSON. The version is `0.1.0`, sourced from the package version in `pyproject.toml` through the application configuration.

## Prometheus metrics

`GET /metrics` exposes `atlas_http_requests_total` and
`atlas_http_request_duration_seconds` in Prometheus text format on the existing
application port `5000`. The request counter and latency histogram use only
`method`, `route`, and `status` labels. Methods outside the common HTTP
allowlist are recorded as `OTHER`; routes use Flask's matched route template,
and unknown routes use the constant `unmatched`. Raw paths and query strings
are never used as labels. Requests to `/metrics` are excluded from both
instruments. Health-check requests are included.

The endpoint has no authentication. Keep it within trusted internal access
boundaries: Compose binds the host port to loopback, and the Kubernetes Service
is ClusterIP. Do not expose `/metrics` through a public ingress without adding
an explicit access restriction.

Metrics use an independent in-memory registry for each Flask application
instance. The container currently runs one synchronous Gunicorn worker, so
process-local metrics are complete. Increasing the worker count requires
designing and configuring Prometheus client multiprocess mode, including its
writable metrics directory and worker lifecycle cleanup; multiprocess mode is
not enabled here.

## Structured request logs

Application requests produce one JSON `http.request.completed` event with a UTC
ISO 8601 timestamp, severity, server-generated request ID, normalized HTTP
method, matched route template (or `unmatched`), final status code, and elapsed
milliseconds. The response includes the same ID in `X-Request-ID`; incoming
`X-Request-ID` values are ignored. Successful `/health` and `/metrics` requests
are omitted to reduce probe and scrape noise, while errors for those endpoints
are logged. Other 4xx responses use INFO and 5xx responses use ERROR.

Logs do not include raw paths, query strings, request or response bodies,
headers, cookies, credentials, or exception messages and tracebacks. An
unexpected production exception returns a generic 500 response and records its
exception class with the request event. Development debug mode continues to
propagate exceptions for interactive debugging. Request IDs are for log
correlation only and are not Prometheus labels.

The standard-library JSON handler writes application events to stderr. The
container keeps Gunicorn error logging enabled and disables Gunicorn access logs
so request lines do not create duplicate events or expose query strings. Docker
and Compose capture stdout and stderr, with Compose's existing log rotation.
The current deployment runs one synchronous Gunicorn worker; logs are emitted
per request by the Flask process, and no centralized log collector or durable
log store is configured.

## Run tests and compilation checks

From `app/`, with the environment active:

```bash
python -m pytest
python -m compileall -q src run.py
```

The pytest suite uses Flask's test client and does not start a web server. It
covers endpoint responses, JSON content, package-version consistency, request
logging and privacy, the application factory, and development/production debug
settings.

## Troubleshooting

- **`ModuleNotFoundError: atlas`:** run commands from `app/` and set `PYTHONPATH=src` for direct startup. Pytest reads this source path from `pyproject.toml`.
- **`ModuleNotFoundError: flask` or `pytest`:** activate `.venv-atlas002` and run `python -m pip install -r requirements-dev.txt`.
- **The virtual environment uses a different Python version:** recreate the local environment with Python 3.14 and install `requirements-dev.txt` again.
- **Port 5000 is busy:** stop the other local development server before starting this one.

Local application development and tests need no cloud credentials or registry access. The main-branch CI publication uses GitHub's built-in workflow token, not a user-created credential.

## GitHub Actions CI

The `CI` workflow in `.github/workflows/ci.yml` runs on pushes to `main`, pull requests targeting `main`, and manual dispatch. It uses a GitHub-hosted Ubuntu runner with Python 3.14 and read-only permissions for validation. Outdated runs for the same branch or pull request are cancelled.

The validation job installs `requirements-dev.txt` (which also installs the runtime requirements), compiles the Python sources, runs Ruff's E4/E7/E9/F rules, executes pytest, and checks dependency consistency with `pip check`. It then scans the checked-out source snapshot with the free Gitleaks CLI, builds the existing Dockerfile into a runner-local `linux/amd64` image, and scans that image with Trivy for OS and Python library vulnerabilities. On a push to `main`, it hands the already-scanned image to a separate publishing job only after every check and the CRITICAL gate pass. Pull requests and manual runs validate and scan but do not publish. The workflow needs no AWS credentials, application secrets, or user-created token; it uses the repository's GitHub Actions and Packages configuration.

The workflow pins `actions/checkout` v7.0.1, `actions/setup-python` v7.0.0, `aquasecurity/trivy-action` v0.36.0, `docker/setup-buildx-action` v4.4.1, `docker/build-push-action` v7.4.0, `docker/login-action` v4.6.0, `actions/upload-artifact` v7.0.2, and `actions/download-artifact` v8.0.2 to full commit SHAs. It uses Ruff 0.17.1, Gitleaks 8.30.1 (verified against the official Linux x64 release checksum), and Trivy CLI 0.76.1. The Trivy action caches its CLI and vulnerability database; Python dependencies are not cached.

The Dockerfile pins the official `python:3.14.9-slim-trixie` base image by digest `sha256:0214bda9af2652a418f2bf34373a4d3ca00a5f4784081e040049433ac9cc79d5`. CI separately builds the application image for `linux/amd64`. The repository does not document validation for other build targets.

The Trivy policy reports every HIGH and CRITICAL result in the Actions step log and the run summary. It fails only when at least one CRITICAL finding is present. `ignore-unfixed` remains false and no vulnerability ignore or suppression list is configured. HIGH findings are temporarily non-blocking because the controlled 2026-10-22 comparison with the tested base reported 48 HIGH findings after the base-image change; making HIGH blocking immediately would prevent the first CI run before that baseline can be triaged. The findings remain visible for remediation and are not treated as accepted or harmless. Tighten the policy by making any HIGH finding fail once the HIGH baseline has been reduced and reviewed.

The controlled comparison used local Trivy 0.71.1 and the same cached vulnerability database, refreshed 2026-10-22 07:10 UTC, for both images. The original image had 65 HIGH and 3 CRITICAL findings; the tested candidate had 48 HIGH and 0 CRITICAL findings. Candidate HIGH IDs included `CVE-2025-69720`, `CVE-2026-16742`, `CVE-2026-54369`, `CVE-2026-76642`, `CVE-2026-78408`, `CVE-2026-78409`, `CVE-2026-78410`, `CVE-2026-9538`, `GHSA-6v7p-g79w-8964`, `CVE-2025-47273`, `CVE-2026-97687`, and `CVE-2026-97689`. Trivy listed no fixed versions for the remaining Debian findings. It warned that third-party SBOM data can be inaccurate: the experiment confirmed msgpack and urllib3 within pip's vendored files, while its setuptools SBOM record was not found in the final image filesystem. These findings remain visible in CI. Zero CRITICAL findings does not mean the image is vulnerability-free; HIGH findings remain, and the CI Trivy 0.76.1 database can produce counts different from the local Trivy 0.71.1 snapshot.

### GHCR image publication

Successful pushes to `main` publish `ghcr.io/avinashmnth2507-dev/project-atlas:sha-<full-commit-sha>`, for example `sha-ccef0756d94bd707f2b44481bb6fdfd10eed9a4f`. The repository name is lowercase. No `main` or `latest` convenience tag is published. The full-SHA tag identifies the source commit; GHCR tags can still be moved by another push, so use the manifest digest for strict image pinning.

The validation job builds the `linux/amd64` image once with Buildx, loads it locally, and scans it with Trivy. If all validation steps and the CRITICAL gate succeed on a push to `main`, the workflow saves that scanned image to a one-day GitHub Actions artifact. A dependent publish job downloads and loads the same image archive, then pushes its SHA tag. Pull requests and manual dispatches do not upload the image artifact or publish to GHCR. A failed check, failed Trivy gate, or failed artifact transfer prevents the publish job from running. The image remains subject to the documented HIGH findings; they are visible and non-blocking, not suppressed.

Only the publish job receives `packages: write`. It logs in to `ghcr.io` with `github.actor` and GitHub's built-in `GITHUB_TOKEN`; the validation job retains `contents: read`. The token value is not passed as a build argument, stored in the image, or printed in logs. The image archive contains the image only and is retained for one day to hand off the scanned build without rebuilding it.

After a successful publish, replace the tag placeholder with the full commit SHA, then inspect the tag and its registry manifest digest:

```bash
IMAGE=ghcr.io/avinashmnth2507-dev/project-atlas
TAG='sha-<full-commit-sha>'
docker buildx imagetools inspect "$IMAGE:$TAG"
```

Copy the `Digest` value from the output, replace the digest placeholder, then pull by digest:

```bash
IMAGE=ghcr.io/avinashmnth2507-dev/project-atlas
DIGEST='sha256:<manifest-digest>'
docker pull "$IMAGE@$DIGEST"
```

The push step also prints the published digest in its Actions log. To verify a publication, open the account's **Packages** list, select `project-atlas`, and confirm the `sha-<full-commit-sha>` version, linked repository, and digest. Public GHCR packages can be pulled anonymously; private packages require an authorized login. A newly published package is private by default. Review visibility and package access manually in GitHub under the package's **Package settings**; making a package public is a manual choice, and GitHub does not allow changing it back to private. See GitHub's [package visibility and access documentation](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility). Publishing from this repository's workflow with `GITHUB_TOKEN` associates the package with this repository. Before first publish, verify that repository and organization Actions policy permits the publish job's `packages: write` token permission. If a package already exists, check its **Manage Actions access** settings to ensure this repository's workflow can publish. See GitHub's [GITHUB_TOKEN package workflow guidance](https://docs.github.com/en/packages/managing-github-packages-using-github-actions-workflows/publishing-and-installing-a-package-with-github-actions).

The tracked screenshot [19-ghcr-image-published.png](../screenshots/05-ghcr/19-ghcr-image-published.png) records the initial successful publication. It is historical evidence and does not establish that the latest source commit has a published image.

View results in the repository's **Actions** tab and open the `CI` run for step-level logs. A local test or lint success is useful feedback, but it does not establish that a GitHub-hosted workflow run passed; report CI as verified only after an actual run appears in Actions.

### Investigate a failed CI step

- **Python compilation or tests:** from `app/`, run `./.venv-atlas002/bin/python -m compileall -q src tests run.py` and `./.venv-atlas002/bin/python -m pytest -q`; inspect the failing file and assertion in the job log.
- **Ruff:** from `app/`, run `./.venv-atlas002/bin/python -m ruff check --select E4,E7,E9,F src tests run.py`. Correct the reported code issue and rerun the check.
- **Dependency consistency:** from `app/`, run `./.venv-atlas002/bin/python -m pip check`; compare the conflicting package versions with `requirements.txt` and `requirements-dev.txt`.
- **Docker build:** from the repository root, run `docker build --platform linux/amd64 --tag atlas-api:ci --file Dockerfile .` and inspect the first failing build step.
- **Gitleaks:** review the redacted finding and remove the exposed value from the checked-out files. Revoke or rotate a real credential; do not paste it into logs or an issue. This scan checks the checked-out source snapshot, not the full Git history.
- **Trivy:** inspect the CVE/GHSA, package, installed version, fixed version, and whether the package is part of the image. Update the application dependency or pinned base image as appropriate. The workflow has no finding suppressions or ignore entries; Trivy's database changes over time, so findings can change between runs. A zero-CRITICAL result does not establish that the image is vulnerability-free.

The tracked screenshot [18-ci-run-success.png](../screenshots/05-github-actions/18-ci-run-success.png) records an earlier successful GitHub-hosted CI run. Local validation does not establish the result of a later workflow run; check the Actions page for the commit being reviewed.

## Build and run the local Docker image

From the repository root, build the current checkout and start only the Atlas API:

```bash
docker compose -f compose.yaml up --build --detach api
docker compose -f compose.yaml ps
curl --fail http://127.0.0.1:5055/health
```

Compose's image value `project-atlas-api:0.1.0-atlas003-6461902` is a local tag paired with the Dockerfile build context; it does not identify a source commit. `--build` ensures the image is built from the current checkout. The Dockerfile pins the official Python 3.14.9 slim Trixie base image by digest `sha256:0214bda9af2652a418f2bf34373a4d3ca00a5f4784081e040049433ac9cc79d5`. CI separately targets `linux/amd64`; the repository does not document validation for other build targets. The image installs only production requirements and copies the application into `/opt/atlas`. It starts Gunicorn with one synchronous worker, disables Gunicorn's optional control socket, runs as UID/GID `10001`, and has a Python standard-library health check for `/health`.

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
