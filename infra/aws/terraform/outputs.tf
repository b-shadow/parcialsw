output "api_url" {
  value = "https://${var.api_domain}"
}

output "frontend_url" {
  value = "https://${var.frontend_domain}"
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "artifacts_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}
