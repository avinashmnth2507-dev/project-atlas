# 6. Deployment architecture

Atlas has three deployment descriptions with different scopes: Docker Compose
for the local container, Kustomize for the historical local Kubernetes test,
and Helm as an alternative package for the same Kubernetes workloads. Terraform
is only a provider configuration foundation and is not a deployment path yet.

## Docker Compose

`compose.yaml` builds the root Dockerfile and maps `127.0.0.1:5055` on the host
to port `5000` in the container. Use `--build` when starting the service so
the local image is built from the checked-out source. The configured tag
`project-atlas-api:0.1.0-atlas003-6461902` is a local label; it does not identify
the current source revision or a GHCR digest.

The image uses a Python `3.14.9-slim-trixie` base pinned by digest, copies only
the Atlas package, and runs Gunicorn as UID/GID `10001`. CI separately builds
the application image for `linux/amd64`; the repository does not document
validation for other build targets. The container starts one synchronous
worker, disables its control socket, keeps Gunicorn error logging, and has a
`/health` Docker health check. Gunicorn request access logging is disabled
because the Flask app emits structured request events.

Compose adds the runtime controls: loopback host binding, read-only root,
`/tmp` tmpfs with `noexec,nosuid` and `16m` size, all capabilities dropped,
`no-new-privileges`, PID limit `64`, one CPU, `256m` memory, and JSON-file log
rotation (`5m`, two files). These settings do not constitute a production
multi-host deployment or an external availability boundary.

## Kustomize and the recorded local test

`kubernetes/kustomization.yaml` composes `atlas-api.yaml`, which defines:

- Namespace `atlas` with `pod-security.kubernetes.io/enforce=restricted`.
- Deployment `atlas-api`, one replica, port `5000`, and startup, readiness, and
  liveness HTTP probes on `/health`.
- ClusterIP Service `atlas-api` on port `5000`.
- Non-root UID/GID/fsGroup `10001`, RuntimeDefault seccomp, no service-account
  token automount, no privilege escalation, read-only root, dropped
  capabilities, and a memory-backed `/tmp` volume capped at `16Mi`.
- CPU request `100m`, memory request `96Mi`, CPU limit `1`, and memory limit
  `256Mi`.

A local deployment and four-endpoint smoke test were completed using the
dedicated `atlas-smoke` Minikube profile with Kubernetes `v1.35.1`, two CPUs,
and `2048MiB`. Host access used a loopback-only port-forward on port `5060`.
The evidence file is
[20-kubernetes-local-smoke-test.png](../../screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png).
This is historical evidence; it does not establish the cluster's current
state.

The manifest and chart now pin
`ghcr.io/avinashmnth2507-dev/project-atlas@sha256:32cec7ad8da3303f038b15ca2b6369f6c86ba28c7ed8d4709ae164df729af5fa`,
verified for source tag
`sha-989de965f9ea04f1f4292fa6c819aeb49daa8f31`. The historical smoke test
used the earlier image from source tag
`sha-d66b09be89258e0898ef559fc5c7b8e71b5ece32`, before metrics and JSON
logging. Repeat the smoke test against the current pin before claiming these
features have been validated in Kubernetes.

The Kustomize `Namespace` is managed by the manifest. Do not assume deleting
or replacing the application also deletes the namespace; review its full
contents before any namespace cleanup.

## Helm alternative and workload ownership

`helm/atlas/` renders the same `atlas-api` Deployment and Service with the same
image digest, one-replica default, labels, selectors, probes, resource values,
and security settings. The chart uses `.Release.Namespace` and deliberately
does not template a Namespace. Before a Helm release, namespace `atlas` must
already exist with the restricted PSA label.

Kustomize and Helm are alternatives. Never use them as simultaneous managers
of the same Deployment and Service, and do not use Helm to take over
Kustomize-managed resources. A migration requires a reviewed ownership
handoff or a separate namespace. Chart lint and template commands have been
used offline; no Helm install or upgrade is claimed.

## Image release flow

The GitHub Actions workflow builds and scans the image, then on successful
`main` pushes transfers that same image through a short-lived artifact to a
publish job. The publish job pushes the full-commit-SHA tag to GHCR. Kubernetes
manifests pin a separate digest rather than consuming a mutable tag. Updating
that digest is a manual reviewed step. The committed pin now references the
verified image for source commit
`989de965f9ea04f1f4292fa6c819aeb49daa8f31`; publishing a later tag will not
automatically update either deployment definition.

The workflow builds the application image for `linux/amd64`. The Dockerfile's
immutable Python base-image digest is a separate setting; the repository does
not document validation for other build targets.

## Terraform and AWS

Terraform is configured for AWS region `ap-southeast-2` and the AWS provider,
with provider lock version `6.70.0`. No resources, data sources, modules, or
backend are defined. No account, credentials, remote state, VPC, cluster, or
AWS-hosted Atlas service is represented. A future cloud deployment needs a
separate design, state and credential plan, cost review, and explicit resource
definitions.

## Offline versus live validation

`kubectl kustomize` renders YAML locally. `helm lint` and `helm template`
validate chart structure and output. None of these check API-server admission,
scheduling, image pulls, actual readiness, or endpoint responses in a running
cluster. The recorded Minikube smoke test is separate historical evidence and
was executed before the latest metrics and logging source changes.
