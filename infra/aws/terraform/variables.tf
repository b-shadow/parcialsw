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
  description = "URI ECR completa de la imagen backend, por ejemplo 123456789012.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend:latest."
}

variable "frontend_bucket_name" {
  type        = string
  description = "Nombre global unico del bucket S3 del frontend."
}

variable "frontend_external_url" {
  type        = string
  default     = "https://case-inteligente.vercel.app"
  description = "URL externa del frontend cuando CloudFront esta deshabilitado, por ejemplo Vercel."
}

variable "frontend_allowed_origins" {
  type = list(string)
  default = [
    "https://case-inteligente.vercel.app",
    "https://case-inteligente-v2.vercel.app",
  ]
  description = "Origins adicionales permitidos para CORS en el backend."
}

variable "enable_cloudfront" {
  type        = bool
  default     = false
  description = "Habilita S3 + CloudFront para el frontend. Requiere cuenta AWS verificada para CloudFront."
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

variable "jwt_secret_arn" {
  type        = string
  description = "ARN de Secrets Manager con el secreto JWT como texto."
}

variable "mongodb_uri_secret_arn" {
  type        = string
  description = "ARN de Secrets Manager con una URI MongoDB administrada, TLS y acceso restringido a esta VPC."
}

variable "mongodb_database" {
  type    = string
  default = "case_inteligente_nosql"
}

variable "ollama_base_url" {
  type        = string
  default     = null
  description = "URL privada del servicio Ollama; debe ser alcanzable desde la EC2."

  validation {
    condition     = var.enable_aws_ollama || (var.ollama_base_url != null && length(trimspace(var.ollama_base_url)) > 0)
    error_message = "Configure ollama_base_url o active enable_aws_ollama."
  }
}

variable "enable_aws_ollama" {
  type        = bool
  default     = false
  description = "Crea una EC2 GPU para Ollama. Desactivado por defecto por su costo."
}

variable "ollama_instance_type" {
  type        = string
  default     = "g6.xlarge"
  description = "Tipo de instancia GPU para Ollama; confirmar disponibilidad y cuota regional."
}

variable "redis_url_secret_arn" {
  type        = string
  default     = null
  description = "ARN opcional de Secrets Manager con URL Redis privada. Sin este valor, Redis queda desactivado."
}

variable "rds_backup_retention_period" {
  type        = number
  default     = 7
  description = "Dias de retencion de backups RDS; en produccion nunca debe ser cero."

  validation {
    condition     = var.rds_backup_retention_period >= 1 && var.rds_backup_retention_period <= 35
    error_message = "La retencion RDS debe estar entre 1 y 35 dias."
  }
}

variable "backup_archive_retention_days" {
  type    = number
  default = 30

  validation {
    condition     = var.backup_archive_retention_days >= 7
    error_message = "Los respaldos coordinados deben conservarse al menos 7 dias."
  }
}

variable "alarm_email" {
  type        = string
  default     = null
  description = "Correo opcional para alarmas de EC2, ALB y RDS; requiere confirmar la suscripcion SNS."
}

variable "ec2_instance_type" {
  type        = string
  default     = "t3.small"
  description = "Tipo de instancia EC2 para ejecutar el backend Docker."
}

variable "ec2_key_name" {
  type        = string
  default     = null
  description = "Nombre de key pair EC2 para SSH. Puede quedar null si se usa Session Manager."
}

variable "admin_ssh_cidr" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR autorizado para SSH si se habilita el puerto 22."
}

variable "enable_ssh" {
  type        = bool
  default     = false
  description = "Habilita acceso SSH a la instancia EC2. Recomendado false y usar SSM Session Manager."
}
