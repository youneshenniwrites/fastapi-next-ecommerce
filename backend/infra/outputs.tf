output "alb_dns_name" {
  value = aws_lb.app.dns_name
}

output "fastapi_url" {
  value = "http://${var.domain_name}"
}
