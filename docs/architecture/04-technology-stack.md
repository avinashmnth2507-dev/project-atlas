# 4. Technology stack

Versions below come from committed manifests, dependency files, CI settings,
or CLI versions observed during the repository review. Environment-specific
CLI observations are not requirements for every checkout.

| Purpose | Technology | Version or constraint | Use in Atlas |
| --- | --- | --- | --- |
| Language | Python | `>=3.14`; CI uses `3.14`; Docker base is `3.14.9` | API implementation, tests, and CI |
| API framework | Flask | `3.1.3` runtime pin; `>=3.1,<4.0` project range | Application factory, JSON routes, hooks |
| WSGI server | Gunicorn | `26.1.0` runtime pin; `>=26.1,<27.0` project range | One synchronous container worker |
| Metrics client | prometheus-client | `0.26.0` runtime pin; `>=0.26,<0.27` project range | Counter, histogram, and text exposition |
| Test runner | pytest | `>=8` in development requirements | Flask test-client coverage |
| Linter | Ruff | `0.17.1` pinned in development requirements | CI checks E4, E7, E9, and F rules |
| Container base | Python slim Trixie | `python:3.14.9-slim-trixie` pinned by digest; CI builds `linux/amd64` | Reproducible build input for the API image |
| Local container runtime | Docker | CLI `24.0.6` observed; repository does not pin Docker or Compose CLI versions | Compose loopback container runtime |
| CI platform | GitHub Actions | Ubuntu `24.04`, Python `3.14` | Test, scan, build, and publish workflow |
| Source scanner | Gitleaks | `8.30.1`, release checksum verified by CI | Tracked-source secret scan |
| Image scanner | Trivy CLI | `0.76.1` in CI | HIGH/CRITICAL OS and library scan |
| Kubernetes | Kubernetes | `v1.35.1` in the recorded local smoke test | Local Deployment and Service validation |
| Kubernetes client | kubectl / Kustomize | kubectl `v1.37.1`; Kustomize `v5.8.1` observed | Render/apply/read Kubernetes resources |
| Local cluster tool | Minikube | `v1.38.1` observed | Dedicated `atlas-smoke` profile used historically |
| Packaging | Helm | CLI `v4.1.4` observed; chart API `v2` | Render/lint alternative workload packaging |
| Infrastructure as code | Terraform | `1.16.4` observed; required `>=1.16.0,<1.17.0` | Provider-only foundation; no resources |
| Cloud provider plugin | hashicorp/aws | Constraint `~>6.0`; lock selection `6.70.0` | AWS provider configuration only |

The local Python virtual environment documented by the application README used
Python `3.14.8`. CLI versions are environment observations rather than
repository requirements unless listed as constraints above.

## Runtime dependencies

`app/requirements.txt` pins Flask, Gunicorn, `prometheus-client`, and Flask's
runtime dependencies. `app/pyproject.toml` describes the supported version
ranges. `app/requirements-dev.txt` includes the runtime pins, pytest, and Ruff.
Request logging uses the Python standard library (`logging`, `json`, `datetime`,
`time`, and `uuid`); it adds no logging package.

## Infrastructure and observability selection

Kubernetes resources are plain YAML rendered with Kustomize. The Helm chart
renders the same Deployment and Service with a fixed digest default. Neither
tool provisions cloud resources. Terraform selects the AWS provider and
`ap-southeast-2` region only; no account, state backend, or resource is
configured.

The application exports metrics, but no Prometheus or Grafana deployment is
present. It emits JSON request events to stderr, but no Loki, Fluent Bit,
Promtail, Elasticsearch, or other collector is configured. Ansible and Jenkins
are not implemented. The old root README's broad tool list described an
aspiration, not the actual tracked stack.

## Image compatibility

CI builds the application image for `linux/amd64`, while the Dockerfile pins
the Python base image by digest. These are separate configuration choices.
The Kubernetes and Helm image reference is also immutable, but it is an older
release from before metrics and structured logs. Digest pinning ensures
repeatability, not freshness. Review and update the image digest in both
deployment alternatives after publishing a current image. The repository does
not document validation for other build targets.
