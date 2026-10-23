# Project Atlas on Kubernetes

This directory contains the first local Kubernetes foundation for the stateless
Flask API. It does not define an Ingress, external load balancer, persistent
storage, cloud resources, or application secrets.

## Recorded deployment status

ATLAS-006 completed a local smoke test on the isolated Minikube profile
`atlas-smoke`, using Kubernetes `v1.35.1`, two CPUs, and `2048MiB`. The
Deployment became available, and `/`, `/health`, `/info`, and `/version`
returned HTTP 200 through a loopback-only port-forward on `127.0.0.1:5060`.
The [tracked screenshot](../screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png)
is historical evidence; this guide does not assert that the profile is running
now.

The tested image and the current manifest image are from the earlier GHCR
release below. They predate the later `/metrics` and structured JSON logging
changes in the current application source. The smoke-test screenshot does not
validate those later features in Kubernetes. Publish and review a current image
digest, update this manifest and the Helm default, then repeat the test before
making that claim.

## Resources

`kustomization.yaml` is the offline Kustomize entry point. `atlas-api.yaml`
defines:

- Namespace `atlas`, enforcing the Kubernetes Restricted Pod Security Standard
  where Pod Security Admission is supported.
- One-replica Deployment `atlas-api`, running the API on container port `5000`.
- Internal `ClusterIP` Service `atlas-api` on port `5000`, selecting only the
  Atlas API pods.

The API is stateless. Kubernetes HTTP startup, readiness, and liveness probes
call `/health`; Kubernetes does not consume the Dockerfile's `HEALTHCHECK`.
The probes use generous timeouts and failure thresholds to avoid restarting a
slow-starting process too aggressively.

## Image and GHCR access

The Deployment pins the published image by manifest digest:

```text
ghcr.io/avinashmnth2507-dev/project-atlas@sha256:b4c9a18d1e5d89e964da70a123e8fb9cf84777d15a8f12d8850323db44fb031b
```

This digest was reported by the successful GHCR push for source tag
`sha-d66b09be89258e0898ef559fc5c7b8e71b5ece32`. CI builds `linux/amd64`, which
is the platform built by CI. The Deployment reference does not use `latest` or
any mutable tag. Updating the image requires reviewing and changing the digest
deliberately; this manifest does not rebuild or publish images. Digest pinning
provides repeatability, not freshness; this is not the current app source.

Before deployment, verify the package's visibility in GitHub Packages and that
the cluster can reach `ghcr.io`. A public package needs no pull secret. If the
package is private, create an `imagePullSecret` in namespace `atlas` using an
approved credential with package read access, and reference it from the pod
spec through a secure local process. Never put a token in this repository or
pass it in a command that records it in shell history. No pull secret is
embedded in these manifests.

## Offline rendering and client-side validation

Render the resources locally with Kustomize:

```bash
kubectl kustomize ./kubernetes
```

`kubectl kustomize` parses and renders the Kustomize resources without cluster
access. A `kubectl create --dry-run=client --validate=false` check was attempted
with an empty kubeconfig, but this kubectl client still tried API discovery at
`localhost:8080`; it is therefore not included as a guaranteed offline
validation command. Client-side dry run would not verify API-server admission,
the installed cluster version, scheduling, image pulls, or runtime behavior
anyway. Kustomize rendering confirms YAML parsing and resource composition, but
is not full Kubernetes API-server schema validation or a deployment smoke test.

## Repeat the smoke test

The historical test used an already-created, dedicated `atlas-smoke` profile;
it did not modify the default Minikube profile. Do not assume that profile
still exists or is running. Before repeating the test, update the image digest
to the current reviewed release in the chosen deployment definition and confirm
the cluster state, resources, and namespace ownership.

For a running profile, use the explicit context throughout:

```bash
minikube status -p atlas-smoke
kubectl --context=atlas-smoke get nodes
kubectl --context=atlas-smoke apply -k ./kubernetes
kubectl --context=atlas-smoke -n atlas rollout status deployment/atlas-api --timeout=240s
kubectl --context=atlas-smoke -n atlas get deployments,pods,services -o wide
kubectl --context=atlas-smoke -n atlas port-forward --address 127.0.0.1 service/atlas-api 5060:5000
```

While the port-forward is active, test the four API routes at port `5060`.
These commands describe a future repeat after the digest update; they were not
run during this documentation change. Do not start, modify, or delete a profile
as part of reading this guide. Review all namespace contents before any cleanup.

```bash
curl --fail http://127.0.0.1:5060/
curl --fail http://127.0.0.1:5060/health
curl --fail http://127.0.0.1:5060/info
curl --fail http://127.0.0.1:5060/version
```

## Security and Docker differences

The pod runs as non-root UID/GID `10001`, disables privilege escalation,
uses a read-only root filesystem, drops all Linux capabilities, and requests
the runtime's default seccomp profile. The pod does not receive a Kubernetes
service-account token. A memory-backed `/tmp` volume is capped at `16Mi` to
provide the temporary write area needed by Gunicorn. CPU and memory requests
and limits are set for a single-node local cluster.

These controls carry over Compose's non-root user, read-only root, dropped
capabilities, no-new-privileges behavior, temporary `/tmp`, and CPU/memory
limits. Kubernetes has no portable per-pod PID limit or standard `emptyDir`
mount flags equivalent to Compose's `noexec,nosuid`; cluster-level policy is
needed for those controls. Compose's loopback port mapping is replaced by an
internal Service; use a local port-forward for host access. Container log
rotation remains a cluster logging/runtime concern. The current Kustomize
image predates application-level Prometheus metrics and JSON request logs; the
Kubernetes resources do not deploy a scraper or log collector.

## Evidence

The genuine local smoke-test evidence is already tracked at
`screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png`. It records the
historical deployment above and should not be presented as evidence of the
current image digest or current cluster state.
