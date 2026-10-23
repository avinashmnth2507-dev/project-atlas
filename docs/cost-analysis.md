# Cost and cloud scope

No cost model has been completed for Project Atlas. The Terraform directory
contains only an AWS provider configuration and region variable; it defines no
AWS resources and does not configure an account or state backend. No AWS
deployment or resource creation is part of the current implementation.

The local Compose and Minikube configurations consume developer-machine
resources. GitHub Actions and GHCR usage depends on account configuration,
retention, and service terms; this repository does not calculate those costs.
Do not describe Atlas as cost-free in general based only on the absence of
Terraform resources.

Before adding AWS resources, estimate cost for the reviewed architecture and
deployment duration, configure budget alerts and ownership, and define
Terraform state and credential handling. See the
[Terraform scope](../ARCHITECTURE.md#terraform-scope) and
[deployment architecture](architecture/06-deployment-architecture.md).
