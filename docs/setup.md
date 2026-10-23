# Local setup

The application setup guide is maintained in
[app/README.md](../app/README.md#create-a-local-environment).

From the repository root, the shortest development setup is:

```bash
cd app
python3.14 -m venv .venv-atlas002
source .venv-atlas002/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

This installs Python application and development packages into the local
virtual environment. It does not start Docker, Minikube, Kubernetes, or AWS
resources. For routes and the loopback-bound Flask development command, see
the [application guide](../app/README.md).
