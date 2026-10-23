# 7. Roadmap and milestone history

The milestones below describe repository changes and recorded local checks.
“Complete” means the scoped artifact was implemented or the named evidence was
captured; it does not imply a production service, continuous deployment to
AWS, or a currently running local cluster.

## Completed milestones

| Milestone | Delivered scope | Evidence |
| --- | --- | --- |
| ATLAS-001 | Repository and workstation foundation, initial project structure, Git history | [Foundation screenshots](../../screenshots/01-foundation/01-devops-workstation-check.png), [project structure](../../screenshots/01-foundation/03-project-folder-structure.png) |
| ATLAS-002 | Python package and Flask backend foundation, configuration, API routes, tests | [Python setup](../../screenshots/02-python/07-python-virtual-environment.png), [API checks](../../screenshots/03-backend/16-api-endpoints-tested.png) |
| ATLAS-003 | Local Docker image and hardened Compose service | [Container evidence](../../screenshots/04-docker/17-docker-container-healthy.png) |
| ATLAS-004 | GitHub Actions validation and container security scanning | [Successful CI run evidence](../../screenshots/05-github-actions/18-ci-run-success.png) |
| ATLAS-005 | Conditional GHCR publication of scanned full-commit-SHA images | [Initial GHCR publication](../../screenshots/05-ghcr/19-ghcr-image-published.png) |
| ATLAS-006 | Restricted Kubernetes manifests and isolated local Minikube smoke test | [Kubernetes smoke-test evidence](../../screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png) |
| ATLAS-007 | Terraform versions, AWS provider, `ap-southeast-2` variable, and lockfile; no resources | [Terraform files](../../terraform/versions.tf) |
| ATLAS-008 | Secure Helm chart matching the Kustomize workload; offline lint/render comparison | [Chart](../../helm/atlas/README.md) |
| ATLAS-009 | Per-app Prometheus request counter and latency histogram | [Metrics implementation](../../app/src/atlas/metrics.py) |
| ATLAS-010 | JSON request-completion logs, request IDs, safe production 500 responses | [Logging implementation](../../app/src/atlas/logging_config.py) |

Milestone sequence is corroborated by commit history from the July 2026
repository/API foundation through the October 2026 container, delivery,
Kubernetes, Terraform, Helm, and observability commits.

## Current risks and unfinished work

1. **Kubernetes runtime validation is historical.** Kustomize and Helm now pin
   the verified image for source commit
   `989de965f9ea04f1f4292fa6c819aeb49daa8f31`, but the recorded smoke test used
   the earlier image from commit
   `d66b09be89258e0898ef559fc5c7b8e71b5ece32`, before metrics and request
   logging. Repeat the smoke test against the current pin before claiming those
   features in Kubernetes.
2. **HIGH vulnerabilities remain.** The CI workflow reports them without
   blocking; a 2026-10-22 local scan is historical and not a current result.
   Review current findings and reduce the baseline before tightening the gate.
3. **Observability is not collected.** There is no Prometheus scrape target,
   dashboard, alerting, or central log retention. `/metrics` has no
   authentication and should remain behind trusted internal access.
4. **Production exception diagnosis is limited.** General JSON logs omit
   exception messages and tracebacks. Production 500 events expose only the
   exception class and request correlation fields. A secure private diagnostic
   path has not been designed.
5. **No cloud deployment is defined.** Terraform has no resources or backend,
   and there is no AWS account, state, network, cluster, or cost model in the
   repository.
6. **Single-process assumptions remain.** Gunicorn runs one synchronous
   worker. Prometheus multiprocess mode, concurrency behavior, and horizontal
   scaling are not configured.

## Recommended next milestones

1. Deploy the currently pinned image and repeat the isolated `atlas-smoke`
   test. Keep Kustomize and Helm ownership separate.
2. Design a restricted metrics scrape path and log collection/retention
   policy. Add a collector only after access, privacy, storage, and operational
   ownership are settled.
3. Add focused tests for failed health/metrics logging and any desired secure
   diagnostic metadata without placing exception contents in general logs.
4. Define a costed AWS deployment and state/authentication strategy before
   adding Terraform resources or making cloud changes.

These are proposals. They are not part of the current implementation.
