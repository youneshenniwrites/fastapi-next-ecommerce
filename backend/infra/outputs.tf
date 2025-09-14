output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "fastapi_url" {
  value = "http://${var.domain_name}"
}

output "state_bucket_arn" {
  value = aws_s3_bucket.tf_state.arn
}

output "dynamodb_lock_table_arn" {
  value = aws_dynamodb_table.tf_lock.arn
}
