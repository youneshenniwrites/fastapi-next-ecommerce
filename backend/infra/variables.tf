variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "container_image" {
  description = "Docker image for FastAPI app"
  type        = string
  default     = "your-dockerhub-user/fastapi:latest"
}

variable "db_password" {
  description = "Database password for FastAPI app"
  type        = string
  sensitive   = true
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name for FastAPI app"
  type        = string
}

variable "state_bucket_name" {
  type        = string
  default     = "fastapi-terraform-state-bucket"
  description = "S3 bucket name for Terraform state"
}

variable "dynamodb_table_name" {
  type        = string
  default     = "terraform-locks"
  description = "DynamoDB table name for state locking"
}
