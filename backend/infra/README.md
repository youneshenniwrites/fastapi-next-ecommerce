# Legacy AWS infrastructure

This folder contains the original, incomplete AWS Terraform. These files are
historical reference and are not the approved deployment path. Do not run them
as part of local setup.

The old workflow in backend/.github/workflows/terraform.yml is also legacy and is
not an active root GitHub Actions workflow. Do not promote it into an active workflow.

See [the approved hosting plan](../../docs/architecture.md#approved-free-demo-hosting)
and [environment runbook](../../deploy/environments/README.md) for Vercel and Neon.
Azure is an optional future migration (#31). No cloud resources are managed here.
