# 🚀 Project Atlas

> A Production-Grade Internal Developer Platform built from scratch using modern DevOps and Platform Engineering practices.

## 📌 Project Goal

Project Atlas is an end-to-end DevOps portfolio project designed to demonstrate production-ready skills in:

- Linux
- Git & GitHub
- Python
- Docker
- Kubernetes
- Helm
- Terraform
- Ansible
- Jenkins
- GitHub Actions
- AWS
- Prometheus
- Grafana
- Loki
- DevSecOps

This project is being built step by step to simulate how modern engineering teams design, build, deploy, monitor, and secure cloud-native applications.

---

## 🛠️ Tech Stack

- Python
- Docker
- Kubernetes
- Terraform
- AWS
- Ansible
- Jenkins
- GitHub Actions
- Prometheus
- Grafana
- Loki
- Helm
- Git

---

## 📂 Project Structure

```text
app/
docker/
kubernetes/
terraform/
ansible/
jenkins/
monitoring/
logging/
security/
docs/
diagrams/
scripts/
tests/
```

---

## 📈 Project Status

The backend foundation is implemented as a small Flask application with an application factory and four GET endpoints: `/`, `/health`, `/info`, and `/version`. A local Docker image runs the API with Gunicorn as a non-root user and binds to loopback by default. GitHub Actions CI is configured to validate the Python API and build and scan the image without publishing it. See [app/README.md](app/README.md) for local commands and pipeline details.

Kubernetes, Terraform, deployment automation, monitoring, logging, and broader security components remain planned and are not implemented yet.

---

## 👨‍💻 Author

**Avinash Mani Tripathi**
