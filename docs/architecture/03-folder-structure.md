# 3. Repository structure

This is a selective view of tracked paths and their purposes, not a complete
file listing. It omits ignored virtual environments, caches, and other
workspace-only files.

```text
.
├── .github/
│   └── workflows/ci.yml
├── app/
│   ├── .env.example
│   ├── README.md
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── run.py
│   ├── src/
│   │   ├── atlas/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── extensions.py
│   │   │   ├── logging_config.py
│   │   │   ├── metrics.py
│   │   │   └── api/
│   │   │       ├── home.py
│   │   │       ├── health.py
│   │   │       ├── info.py
│   │   │       └── version.py
│   │   └── atlas.egg-info/
│   └── tests/test_api.py
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── architecture/
│   │   ├── 01-project-overview.md
│   │   ├── 02-system-architecture.md
│   │   ├── 03-folder-structure.md
│   │   ├── 04-technology-stack.md
│   │   ├── 05-development-workflow.md
│   │   ├── 06-deployment-architecture.md
│   │   └── 07-roadmap.md
│   ├── cost-analysis.md
│   ├── deployment.md
│   ├── roadmap.md
│   ├── setup.md
│   └── troubleshooting.md
├── helm/atlas/
│   ├── Chart.yaml
│   ├── README.md
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       └── service.yaml
├── kubernetes/
│   ├── README.md
│   ├── kustomization.yaml
│   └── atlas-api.yaml
├── screenshots/
│   ├── 01-foundation/
│   ├── 02-python/
│   ├── 03-backend/
│   ├── 04-docker/
│   ├── 05-github-actions/
│   ├── 05-ghcr/
│   └── 07-kubernetes/
├── terraform/
│   ├── versions.tf
│   ├── providers.tf
│   ├── variables.tf
│   └── .terraform.lock.hcl
├── ARCHITECTURE.md
├── Dockerfile
├── compose.yaml
└── README.md
```

## Major paths

- `app/src/atlas/` contains the Flask application factory, configuration,
  route blueprints, request logging, and metrics instrumentation.
- `app/tests/test_api.py` tests route responses, metrics, log content/privacy,
  request IDs, and factory behavior.
- `Dockerfile` defines the hardened image and Gunicorn startup. `compose.yaml`
  defines the local loopback service and its runtime limits.
- `.github/workflows/ci.yml` defines validation, source/image scanning, and
  conditional GHCR publishing.
- `kubernetes/` contains Kustomize input and a Namespace, Deployment, and
  Service. The Deployment pins the verified GHCR image for source commit
  `989de965f9ea04f1f4292fa6c819aeb49daa8f31`.
- `helm/atlas/` contains the alternative Helm chart for the Deployment and
  Service. It does not create the Namespace.
- `terraform/` contains only Terraform/provider constraints, AWS provider
  configuration, a region variable, and the provider lock file. No AWS
  resources are defined.
- `screenshots/` contains tracked historical evidence files. Screenshots do
  not establish the current state of external systems.
- `docs/` contains this documentation set and topic navigation pages.

`diagrams/` is not a tracked directory in Git. Architecture diagrams are kept
as Mermaid source in Markdown so GitHub can render and review them with the
documentation.

The repository also tracks `app/src/atlas.egg-info/` package metadata files.
The CI workflow scans tracked source files, not local ignored environments.

The tracked root files `CHANGELOG.md`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, and `LICENSE` are empty in this revision. The project has
not yet established release-note, contribution, conduct, or license text in
those placeholders.
