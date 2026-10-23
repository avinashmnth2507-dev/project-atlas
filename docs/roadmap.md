# Roadmap

The canonical milestone history, current risks, and proposed next work are
maintained in [architecture chapter 7](architecture/07-roadmap.md). This page
remains as a short link for the original `docs/roadmap.md` location.

The next release-level task is to repeat the local Kubernetes smoke test
against the verified image currently pinned by Kustomize and Helm. The existing
smoke-test evidence records the earlier image and does not validate the current
metrics and JSON request logging behavior in a cluster.
