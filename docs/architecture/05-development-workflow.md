# 5. Development workflow

## Clone and prepare the application

```bash
git clone https://github.com/avinashmnth2507-dev/project-atlas.git
cd project-atlas/app
python3.14 -m venv .venv-atlas002
source .venv-atlas002/bin/activate
python -m pip install -r requirements-dev.txt
```

The development requirements install the runtime dependencies, pytest, and
Ruff. `.venv-atlas002`, other virtual environments, bytecode, test caches,
`.env` files, local Terraform state, variable files, plans, and provider working
directories are excluded by `.gitignore`. `app/.env.example` is currently
empty; do not use it to store credentials.

## Run local checks

From `app/`:

```bash
python -m compileall -q src tests run.py
python -m ruff check --select E4,E7,E9,F src tests run.py
python -m pytest -q
python -m pip check
```

These commands do not start a server or infrastructure. To run the built-in
Flask development server on loopback:

```bash
FLASK_ENV=development PYTHONPATH=src python -m flask \
  --app atlas:create_app run --host 127.0.0.1 --port 5000
```

The separate `python run.py` entry point binds `0.0.0.0:5000`; only use it on a
trusted development network. Neither development server is the production
container server.

## CI workflow

`.github/workflows/ci.yml` runs on pushes to `main`, pull requests targeting
`main`, and manual dispatch. It uses a GitHub-hosted Ubuntu `24.04` runner and
Python `3.14`. The validation job installs development requirements, compiles
Python, runs Ruff, pytest, and `pip check`, scans tracked source with Gitleaks,
builds the image for `linux/amd64`, and scans it with Trivy.

Gitleaks is pinned at `8.30.1` and its official release archive checksum is
checked. Trivy CLI `0.76.1` reports HIGH and CRITICAL findings. HIGH findings
are visible and currently non-blocking; any CRITICAL finding fails the gate.
No vulnerability ignore list is configured. A historical local scan on
2026-10-22 reported 48 HIGH and 0 CRITICAL findings with Trivy `0.71.1` and a
cached database; that is not a current scan result.

## GHCR publication

On a successful push workflow for `main`, CI saves the already-scanned image
to a one-day artifact. A separate `publish` job verifies the artifact SHA-256,
loads that image, logs into GHCR with the job-scoped `GITHUB_TOKEN`, and pushes
`ghcr.io/avinashmnth2507-dev/project-atlas:sha-<full-commit-sha>`. Only this
job has `packages: write`; validation retains `contents: read`. Pull requests
and manual dispatches validate but do not publish. No `main` or `latest` tag is
created. Tags can move; use a reviewed manifest digest for deployment.

The [tracked CI screenshot](../../screenshots/05-github-actions/18-ci-run-success.png)
and [initial GHCR publication screenshot](../../screenshots/05-ghcr/19-ghcr-image-published.png)
document earlier runs, not every future commit.

## Build and run Compose

From repository root:

```bash
docker compose -f compose.yaml up --build --detach api
docker compose -f compose.yaml ps
curl --fail http://127.0.0.1:5055/health
docker compose -f compose.yaml logs --follow api
```

Compose's `image` entry is a local tag and `build` uses the current checkout.
`--build` ensures the container contains the current source. The host port is
loopback-only; the container listens on `5000`. Compose has an existing
read-only filesystem, non-root user, dropped capabilities, no-new-privileges,
PID/CPU/memory limits, `/tmp` tmpfs, and rotating JSON-file logs.

## Kubernetes and Helm validation

Offline checks render local files:

```bash
kubectl kustomize ./kubernetes
helm lint --strict --namespace atlas ./helm/atlas
helm template atlas ./helm/atlas --namespace atlas --kube-version 1.35.1
```

These are not live cluster checks. The local Kustomize smoke test was completed
historically with explicit context `atlas-smoke`; its screenshot is
[here](../../screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png).
The test used the earlier GHCR image from source commit
`d66b09be89258e0898ef559fc5c7b8e71b5ece32`. The current definitions now pin
the verified image from source commit
`989de965f9ea04f1f4292fa6c819aeb49daa8f31`; repeat the smoke test before
claiming Kubernetes runtime validation of metrics or JSON logging.

Kustomize and Helm are mutually exclusive owners of the same Deployment and
Service. Kustomize includes the `atlas` Namespace and its restricted PSA label;
the Helm chart requires that namespace as an existing prerequisite and does
not take it over. Follow the ownership boundary in the
[Kubernetes guide](../../kubernetes/README.md) and
[Helm chart guide](../../helm/atlas/README.md).

## Terraform

Terraform's validated foundation contains the AWS provider selection,
`ap-southeast-2` region variable, version constraints, and committed provider
lock file. There are no resource or backend definitions. The foundation was
initialized with `terraform init -backend=false -input=false` and checked with
`terraform validate -no-color`. No `plan`, `apply`, AWS API call, or resource
creation is part of this workflow.
