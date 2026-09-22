# Infraestructura AWS

## Arquitectura

- Frontend React: S3 privado + CloudFront + ACM + Route53.
- Backend FastAPI: EC2 con Docker detras de Application Load Balancer HTTPS.
- Base de datos: RDS PostgreSQL 16 en subnets privadas con cifrado y backups.
- Artefactos generados: S3 versionado y cifrado.
- Logs: CloudWatch Logs para arranque de EC2 y diagnostico del backend.
- Dominio propio: `frontend_domain` y `api_domain` con registros Route53.

## Variables principales

Copiar `terraform/terraform.tfvars.example` a `terraform.tfvars` y ajustar:

- `domain_name`
- `frontend_domain`
- `api_domain`
- `route53_zone_id`
- `backend_image`
- `frontend_bucket_name`
- `artifacts_bucket_name`
- `database_password`
- `jwt_secret_key`
- `ec2_instance_type`
- `ec2_key_name`
- `enable_ssh`
- `admin_ssh_cidr`

## Flujo

```powershell
cd infra/aws/terraform
terraform init
terraform plan
terraform apply
```

Terraform crea la instancia EC2, instala Docker, hace login a ECR, descarga `backend_image` y ejecuta el backend en el puerto `8000`.

Despues de crear CloudFront:

```powershell
.\scripts\deploy-frontend-s3.ps1 -Bucket case-inteligente-frontend-tu-dominio -CloudFrontDistributionId DISTRIBUTION_ID -ApiBaseUrl https://api.tu-dominio.com/api/v1 -WsBaseUrl wss://api.tu-dominio.com
```

## Seguridad

- RDS no recibe trafico publico.
- Backend solo acepta trafico desde ALB.
- EC2 usa IAM instance profile para ECR, SSM, S3 de artefactos y logs.
- SSH esta deshabilitado por defecto; se recomienda AWS Systems Manager Session Manager.
- Frontend S3 no es publico; CloudFront accede con OAC.
- HTTP redirige a HTTPS.
- Backend emite headers de seguridad y request id.
