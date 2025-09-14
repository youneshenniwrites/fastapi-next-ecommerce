terraform {
  backend "s3" {
    bucket         = "fastapi-terraform-state-bucket" # your unique bucket name
    key            = "infra/terraform.tfstate"        # path inside the bucket
    region         = "us-east-1"                      # your AWS region
    dynamodb_table = "terraform-locks"                # DynamoDB table for locking
    encrypt        = true                             # encrypt state at rest
  }
}
