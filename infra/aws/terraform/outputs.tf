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

output "backend_ec2_instance_id" {
  value = aws_instance.backend.id
}

output "backend_ec2_public_ip" {
  value = aws_instance.backend.public_ip
}

output "backend_target_group_arn" {
  value = aws_lb_target_group.backend.arn
}
