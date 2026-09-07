---
name: ecommerce-azure
description: Plan Azure hosting or infrastructure changes for this ecommerce repository, including the API, future Next.js frontend, and PostgreSQL.
---

Azure is the chosen cloud provider. Read docs/architecture.md for the proposed
services and distinguish planned infrastructure from resources actually provisioned.
The AWS Terraform in backend/infra is legacy reference, not a starting deployment.

Keep Docker Compose as the local workflow. For cloud work, verify current Azure
service support and regional availability against Microsoft documentation. Plan
container hosting for FastAPI and the future Next.js server, managed PostgreSQL,
image storage, identities/secrets, and logs as one coherent deployment.

Before provisioning, establish the target subscription, region, environment, and
budget within the user's authorization. Include migrations, health checks, and
rollback in the deployment plan. PR merge permission alone does not authorize
cloud spending. Do not copy AWS credentials, state, or resources into an Azure setup.
