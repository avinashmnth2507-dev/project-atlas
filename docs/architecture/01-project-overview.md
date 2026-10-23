# 1. Project overview

## Purpose

Project Atlas is a DevOps and Platform Engineering portfolio project centered
on a small stateless Python API. Its purpose is to make a sequence of
engineering practices reviewable in a repository: application packaging,
automated tests and scans, container hardening, local Kubernetes deployment,
artifact publishing, and a deliberately small observability implementation.

The repository demonstrates these practices on a sample service. It is not a
complete Internal Developer Platform, a production SaaS platform, or a live
AWS environment.

## Audience

The material is intended for engineers, hiring teams, and reviewers who want
to inspect how the API, tests, container, delivery workflow, and local
deployment definitions fit together.

## Implemented scope

- Flask application factory and five routes: four JSON API routes plus
  Prometheus exposition at `/metrics`.
- pytest coverage, Ruff checks, Python compilation, and dependency consistency
  checks in GitHub Actions.
- Gitleaks source scanning and Trivy image scanning with a CRITICAL-only
  blocking gate.
- Digest-pinned Python container, hardened Compose service, and GHCR
  full-commit-SHA publishing workflow.
- Kustomize Kubernetes resources and an alternative Helm chart for one API
  Deployment and internal Service.
- Resource-free AWS provider configuration for `ap-southeast-2`.
- Per-app in-memory Prometheus metrics and privacy-conscious JSON request logs.

## Exclusions

The tracked repository does not implement AWS resources, a database, user
authentication, public ingress, autoscaling, remote Terraform state,
Prometheus/Grafana deployment, centralized log collection, Ansible, Jenkins,
or an internal developer portal control plane. Those systems must not be
inferred from the portfolio goal or from local-only configuration.

## Delivery status

| Area | Status |
| --- | --- |
| Flask endpoints and tests | Implemented in source; exercised with the Flask test client |
| Compose container | Configuration committed; loopback mapping and hardening are defined |
| GitHub Actions and GHCR | Workflow and historical success evidence are committed; latest run is not asserted here |
| Kustomize on Minikube | A historical isolated local smoke test completed; current profile state is unknown |
| Helm | Chart lint/render comparison completed offline; no Helm installation is claimed |
| Terraform | Provider-only foundation validated locally; no resources or AWS account are configured |
| Metrics and request logs | Implemented in current application source and covered by tests |
| Live monitoring and log aggregation | Absent |

The Kubernetes definitions now pin the verified GHCR image for source commit
`989de965f9ea04f1f4292fa6c819aeb49daa8f31`. The historical local smoke test
used the earlier image from commit
`d66b09be89258e0898ef559fc5c7b8e71b5ece32`, before metrics and structured
request logging, so a new cluster smoke test is needed to validate those
features at runtime.

## History and evidence

The implementation sequence is recorded in Git history and the screenshot
directory: initial repository and Python/API foundation; tests and local
container; CI and GHCR publication; local Kubernetes; Terraform; Helm; metrics;
and structured logs. The later milestones map to ATLAS-006 through ATLAS-010.
The [roadmap](07-roadmap.md) gives the milestone list and points to evidence.

## Related documents

- [System architecture](02-system-architecture.md)
- [Repository structure](03-folder-structure.md)
- [Technology stack](04-technology-stack.md)
- [Development workflow](05-development-workflow.md)
- [Deployment architecture](06-deployment-architecture.md)
- [Roadmap](07-roadmap.md)
- [Canonical architecture overview](../../ARCHITECTURE.md)
