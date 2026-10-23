# Deployment options

This page summarizes the checked-in deployment descriptions. It does not
record a currently running container or cluster.

| Path | Purpose | Current boundary |
| --- | --- | --- |
| Docker Compose | Build and run the API locally | Host port binds to `127.0.0.1:5055`; use `--build` for the current checkout |
| Kustomize | Namespace, Deployment, and ClusterIP Service | Defaults pin the verified image for commit `989de965`; recorded smoke test used an earlier image |
| Helm | Alternative templates for the same Deployment and Service | Offline lint/render only; chart does not create or take over the namespace |
| Terraform | AWS provider and region foundation | No resources, backend, account, or deployment |

The complete deployment and ownership rules are in
[architecture chapter 6](architecture/06-deployment-architecture.md). For
component-specific procedures, see the [Kubernetes guide](../kubernetes/README.md)
and [Helm guide](../helm/atlas/README.md). Kustomize and Helm must not manage the
same Deployment and Service simultaneously.

The Kubernetes and Helm definitions now pin the verified image
`ghcr.io/avinashmnth2507-dev/project-atlas@sha256:32cec7ad8da3303f038b15ca2b6369f6c86ba28c7ed8d4709ae164df729af5fa`
from source commit `989de965f9ea04f1f4292fa6c819aeb49daa8f31`. The historical
smoke test used the earlier image from commit
`d66b09be89258e0898ef559fc5c7b8e71b5ece32`; repeat the smoke test against the
current pin before claiming Kubernetes validation of metrics or structured
logging.
