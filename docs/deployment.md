# Deployment options

This page summarizes the checked-in deployment descriptions. It does not
record a currently running container or cluster.

| Path | Purpose | Current boundary |
| --- | --- | --- |
| Docker Compose | Build and run the API locally | Host port binds to `127.0.0.1:5055`; use `--build` for the current checkout |
| Kustomize | Namespace, Deployment, and ClusterIP Service | Local smoke test recorded on `atlas-smoke`; committed image digest is older than metrics/logging source |
| Helm | Alternative templates for the same Deployment and Service | Offline lint/render only; chart does not create or take over the namespace |
| Terraform | AWS provider and region foundation | No resources, backend, account, or deployment |

The complete deployment and ownership rules are in
[architecture chapter 6](architecture/06-deployment-architecture.md). For
component-specific procedures, see the [Kubernetes guide](../kubernetes/README.md)
and [Helm guide](../helm/atlas/README.md). Kustomize and Helm must not manage the
same Deployment and Service simultaneously.

The Kubernetes and Helm definitions currently pin a GHCR image built from
source commit `d66b09be89258e0898ef559fc5c7b8e71b5ece32`. Publish a current
image, review its digest, and update the selected deployment path before
testing the metrics or structured-logging changes in Kubernetes.
