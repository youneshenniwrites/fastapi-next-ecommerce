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
