# 🏗️ Infrastructure - FastAPI on AWS ECS Fargate

This folder contains Terraform code to deploy the FastAPI app to AWS.

## 📋 Prerequisites

- Terraform installed (>=1.5)
- AWS CLI configured with credentials (`aws configure`)
- Docker image built and pushed to ECR

## ⚙️ Configuration

1. Copy the example variables file and update values as needed:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` to set your environment-specific values:

   ```hcl
   region          = "us-east-1"
   container_image = "your-dockerhub-user/fastapi:latest"
   db_password     = "supersecret"
   hosted_zone_id  = "Z1234567890"
   domain_name     = "api.example.com"
   ```

## 🚀 Deployment

1. Navigate to the infra folder:

   ```bash
   cd infra
   ```

2. Initialize Terraform:

   ```bash
   terraform init
   ```

3. Deploy infrastructure:

   ```bash
   terraform apply
   ```

   Terraform will automatically load values from `terraform.tfvars`.

4. After apply, Terraform will output:

   - ALB DNS
   - Deployed FastAPI URL (e.g., `http://api.example.com`)

## 📝 Notes

- The database password is securely stored in **AWS Secrets Manager**.
- To update the app:
  1. Build and push a new Docker image.
  2. Update the `container_image` value in `terraform.tfvars`.
  3. Run `terraform apply` again.
- To destroy all resources:

  ```bash
  terraform destroy
  ```

## 💾 Remote State

This project uses **Terraform remote state** stored in an S3 bucket with **DynamoDB table locking** to prevent concurrent `apply` operations.

- S3 bucket: `fastapi-terraform-state-bucket`
- DynamoDB table: `terraform-locks`
- Defined in `remote_state.tf` and configured in `backend.tf`

Make sure these resources exist (Terraform can also create them on first apply).

## ⚠️ Changing Backend

If you modify the backend (e.g., bucket name or region), run:

```bash
terraform init -reconfigure
```

This ensures Terraform migrates the local state to the remote backend.
