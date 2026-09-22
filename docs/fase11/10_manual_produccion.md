# Manual de Produccion

## Variables

Crear un archivo productivo tomando como base:

`.env.production.example`

Valores clave:

- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `ALLOWED_HOSTS`
- `PUBLIC_API_BASE_URL`
- `PUBLIC_WS_BASE_URL`

## Despliegue AWS

1. Crear repositorio ECR para backend.
2. Publicar imagen backend:

```powershell
.\scripts\aws-deploy.ps1 -AwsAccountId 123456789012 -Region us-east-1 -BackendRepository 123456789012.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend -Tag latest
```

3. Configurar `infra/aws/terraform/terraform.tfvars`.
4. Aplicar infraestructura:

```powershell
cd infra/aws/terraform
terraform init
terraform apply
```

Terraform crea EC2 con Docker, descarga la imagen backend desde ECR y ejecuta el contenedor detras del ALB.

5. Publicar frontend:

```powershell
.\scripts\deploy-frontend-s3.ps1 -Bucket case-inteligente-frontend-tu-dominio -CloudFrontDistributionId DISTRIBUTION_ID -ApiBaseUrl https://api.tu-dominio.com/api/v1 -WsBaseUrl wss://api.tu-dominio.com
```

6. Ejecutar smoke:

```powershell
.\scripts\smoke-test.ps1 -BackendUrl https://api.tu-dominio.com -FrontendUrl https://app.tu-dominio.com
```
