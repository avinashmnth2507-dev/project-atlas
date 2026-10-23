# Documentation index

Use these guides as the entry points for the current repository. Architecture
and deployment notes distinguish committed configuration, offline validation,
historical local evidence, and services that are not implemented.

## Start here

- [Project overview and quick start](../README.md)
- [Canonical architecture](../ARCHITECTURE.md)
- [Milestone roadmap and evidence](architecture/07-roadmap.md)

## Architecture series

1. [Project overview](architecture/01-project-overview.md)
2. [System architecture](architecture/02-system-architecture.md)
3. [Tracked repository structure](architecture/03-folder-structure.md)
4. [Technology stack](architecture/04-technology-stack.md)
5. [Development workflow](architecture/05-development-workflow.md)
6. [Deployment architecture](architecture/06-deployment-architecture.md)
7. [Roadmap](architecture/07-roadmap.md)

The older [`docs/architecture.md`](architecture.md) path is retained as a
short pointer to the root `ARCHITECTURE.md`; it is not a competing architecture
document.

## How-to and component guides

- [Local Python setup](setup.md)
- [Deployment options and ownership](deployment.md)
- [Troubleshooting pointers](troubleshooting.md)
- [Cost and cloud scope](cost-analysis.md)
- [Application routes, tests, metrics, and logs](../app/README.md)
- [Kustomize resources and local smoke-test record](../kubernetes/README.md)
- [Helm chart](../helm/atlas/README.md)
- [Terraform provider foundation](../terraform/versions.tf)
- [GitHub Actions workflow](../.github/workflows/ci.yml)

## Evidence

- [CI run screenshot](../screenshots/05-github-actions/18-ci-run-success.png)
- [Initial GHCR publication screenshot](../screenshots/05-ghcr/19-ghcr-image-published.png)
- [Historical local Kubernetes smoke test](../screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png)

Evidence screenshots record particular earlier steps. They do not establish
the current status of GitHub Actions, GHCR, Docker, Minikube, or a deployed
cluster. In particular, the Kubernetes and Helm manifests pin an image that
predates the current metrics and JSON logging code.

The tracked root files `CHANGELOG.md`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, and `LICENSE` are empty placeholders and therefore are
not listed as active guides here.
