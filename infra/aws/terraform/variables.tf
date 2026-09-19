variable "project_name" {
  type    = string
  default = "case-inteligente"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "domain_name" {
  type        = string
  description = "Dominio raiz propio, por ejemplo ejemplo.com."
}

variable "frontend_domain" {
  type        = string
  description = "Subdominio frontend, por ejemplo app.ejemplo.com."
}

variable "api_domain" {
  type        = string
  description = "Subdominio API, por ejemplo api.ejemplo.com."
}

variable "route53_zone_id" {
  type        = string
  description = "Hosted Zone ID de Route53 para el dominio propio."
}

variable "backend_image" {
  type        = string
  description = "URI ECR de la imagen backend."
}

variable "frontend_bucket_name" {
  type        = string
  description = "Nombre global unico del bucket S3 del frontend."
}

variable "artifacts_bucket_name" {
  type        = string
  description = "Nombre global unico del bucket S3 de artefactos generados."
}

variable "database_name" {
  type    = string
  default = "case_inteligente"
}

variable "database_username" {
  type    = string
  default = "case_user"
}

variable "database_password" {
  type        = string
  sensitive   = true
  description = "Password fuerte para RDS PostgreSQL."
}

variable "jwt_secret_key" {
  type        = string
  sensitive   = true
  description = "Secreto JWT de produccion."
}

variable "desired_backend_count" {
  type    = number
  default = 2
}
