# Project Atlas on Kubernetes

This directory contains the first local Kubernetes foundation for the stateless
Flask API. It does not define an Ingress, external load balancer, persistent
storage, cloud resources, or application secrets.

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
matches the Intel Mac target. The Deployment reference does not use `latest` or
any mutable tag. Updating the image requires reviewing and changing the digest
deliberately; this manifest does not rebuild or publish images.

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

## Optional future Minikube deployment — NOT EXECUTED

The following is a future local-only procedure. It was not run as part of the
offline implementation and requires explicit approval before starting or
changing a cluster. Confirm GHCR access first.

```bash
minikube start --driver=docker --cpus=2 --memory=3072
kubectl apply -k ./kubernetes
kubectl -n atlas rollout status deployment/atlas-api --timeout=120s
kubectl -n atlas get deployment,pods,service
kubectl -n atlas port-forward service/atlas-api 5055:5000
```

While the port-forward is running, use another terminal to check all API routes:

```bash
curl --fail http://127.0.0.1:5055/
curl --fail http://127.0.0.1:5055/health
curl --fail http://127.0.0.1:5055/info
curl --fail http://127.0.0.1:5055/version
```

For cleanup, remove only the Atlas Deployment and Service; this intentionally
leaves the namespace and any other objects untouched:

```bash
kubectl delete deployment atlas-api service atlas-api --namespace atlas --ignore-not-found
```

Do not delete namespace `atlas` unless its contents have been reviewed and are
known to belong exclusively to this project. Do not stop or delete a shared
Minikube profile as part of application cleanup.

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
rotation remains a cluster logging/runtime concern.

## Evidence

After a genuine local deployment and successful smoke test, capture evidence
at `screenshots/07-kubernetes/20-kubernetes-local-smoke-test.png`. Do not create
or present screenshot evidence before those steps have actually succeeded.
