# Roadmap

The canonical milestone history, current risks, and proposed next work are
maintained in [architecture chapter 7](architecture/07-roadmap.md). This page
remains as a short link for the original `docs/roadmap.md` location.

The next release-level task is to publish the current application source,
review its GHCR digest, update the selected Kubernetes definition, and repeat
the local smoke test. The existing Kustomize and Helm image references predate
the current metrics and JSON request logging code.
