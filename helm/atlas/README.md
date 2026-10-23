# Project Atlas Helm chart

This chart renders the existing Project Atlas API Deployment and internal
Service. It does not create a Namespace, cloud resources, secrets, ingress,
storage, or other infrastructure. No cluster deployment is performed as part
of chart development or offline validation.

## Prerequisites and ownership

The target namespace must already exist as `atlas` and carry the Pod Security
Admission label `pod-security.kubernetes.io/enforce=restricted`. Namespace
creation and labeling remain an explicit prerequisite outside this chart.

Helm and Kustomize are alternative deployment methods for the same
`atlas/atlas-api` Deployment and Service. Use only one manager for those
workloads at a time. Do not install this chart over Kustomize-managed resources
or attempt to take over their ownership. A deployment-method change requires a
reviewed ownership handoff or a separate namespace. The chart leaves the
existing namespace ownership untouched.

Render the workloads into the selected Helm namespace with `--namespace atlas`.
The templates use `.Release.Namespace`; they do not create or label that
namespace.

## Defaults

| Value | Default | Purpose |
| --- | --- | --- |
| `replicaCount` | `1` | API replicas |
| `image.repository` | `ghcr.io/avinashmnth2507-dev/project-atlas` | GHCR image repository |
| `image.digest` | `sha256:32cec7ad8da3303f038b15ca2b6369f6c86ba28c7ed8d4709ae164df729af5fa` | Reviewed immutable image digest |
| `resources.requests.cpu` | `100m` | Requested CPU |
| `resources.requests.memory` | `96Mi` | Requested memory |
| `resources.limits.cpu` | `1` | CPU limit |
| `resources.limits.memory` | `256Mi` | Memory limit |

The image template requires a lowercase SHA-256 digest and always renders the
reference as `repository@digest`; there is no tag or `latest` value. Updating
the digest requires deliberate review. The chart contains no registry
credentials. If GHCR access requires a pull secret, manage it through an
approved process outside this chart and repository.

The default digest is the verified GHCR image published for source commit
`989de965f9ea04f1f4292fa6c819aeb49daa8f31`, which includes the current
application's Prometheus endpoint and structured request logging. The
historical Kustomize smoke test used an earlier image; this chart has only been
validated offline and has not deployed the current digest to a cluster.

## Security posture

The chart preserves the Kustomize baseline: restricted namespace PSA
prerequisite; non-root UID/GID `10001`; `fsGroup: 10001`; `RuntimeDefault`
seccomp; disabled service-account token automount; no privilege escalation;
read-only root filesystem; all Linux capabilities dropped; and a memory-backed
`/tmp` volume capped at `16Mi`. Startup, readiness, and liveness probes use
`/health`. CPU/memory requests and limits match the existing manifest.

The Deployment and Service keep the existing names and the three application
labels/selectors. No architecture-specific node scheduling constraints exist
in the current Kubernetes manifest, so none are added by this chart.

## Offline validation

These commands render or lint locally and do not deploy resources:

```bash
helm lint --strict --namespace atlas ./helm/atlas
helm template atlas ./helm/atlas --namespace atlas --kube-version 1.35.1
kubectl kustomize ./kubernetes
```

Compare the rendered Helm Deployment and Service with the Kustomize output by
kind, namespace, and name. Check their specs, labels, selectors, digest,
probes, resources, security settings, ports, volume mounts, and scheduling
constraints. Exclude the Namespace from this comparison because Helm does not
manage it. Helm rendering and linting do not perform Kubernetes API-server
admission or runtime checks.
