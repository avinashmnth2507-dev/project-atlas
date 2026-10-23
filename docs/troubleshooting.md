# Troubleshooting pointers

Use the component guides for commands and context; this page does not assume
that Docker or a Kubernetes profile is currently running.

| Symptom | Start with |
| --- | --- |
| Python import or virtual-environment issue | [Application setup and troubleshooting](../app/README.md#troubleshooting) |
| Test, Ruff, or dependency failure | [Application CI and local checks](architecture/05-development-workflow.md) |
| Compose health or port issue | [Application guide](../app/README.md#build-and-run-the-local-docker-image) |
| Kustomize rendering, image pull, or namespace issue | [Kubernetes guide](../kubernetes/README.md) |
| Helm lint or render issue | [Helm chart guide](../helm/atlas/README.md) |
| Terraform initialization or validation issue | [Terraform workflow](architecture/05-development-workflow.md#terraform) |

The Minikube smoke-test evidence is historical. Check the explicit
`atlas-smoke` profile and cluster context before using Kubernetes commands;
do not assume the default profile or current profile state. The checked-in
Kubernetes image pin now targets source commit
`989de965f9ea04f1f4292fa6c819aeb49daa8f31`; the historical smoke test used an
older image and does not validate the current pin in a cluster.
