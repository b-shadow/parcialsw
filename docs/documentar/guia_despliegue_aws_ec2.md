# Guia exacta de despliegue AWS con EC2

Esta guia reemplaza el despliegue anterior basado en ECS. El backend FastAPI se ejecuta en una instancia EC2 con Docker, detras de un Application Load Balancer HTTPS. El frontend React se mantiene en S3 privado + CloudFront. La base de datos se mantiene en RDS PostgreSQL privado.

## 1. Arquitectura final

- Frontend: S3 privado + CloudFront + ACM + Route53.
- Backend: EC2 Amazon Linux 2023 + Docker + imagen backend desde ECR.
- Balanceador API: Application Load Balancer con HTTPS.
- Base de datos: RDS PostgreSQL 16 en subnets privadas.
- Artefactos generados: S3 versionado y cifrado.
- Acceso administrativo a EC2: Systems Manager Session Manager recomendado.

## 2. Requisitos en la maquina local

Tener instalado:

```powershell
aws --version
```

```powershell
terraform version
```

```powershell
docker --version
```

```powershell
node --version
```

Configurar credenciales AWS:

```powershell
aws configure
```

Verificar identidad:

```powershell
aws sts get-caller-identity
```

## 3. Preparacion en AWS

1. Entrar a AWS Console.
2. Seleccionar la region que se usara, por ejemplo `us-east-1`.
3. Tener un dominio administrado en Route53.
4. Copiar el Hosted Zone ID del dominio.
5. Crear repositorio ECR para backend:

```powershell
aws ecr create-repository --repository-name case-inteligente-backend --region us-east-1
```

6. Obtener el Account ID:

```powershell
aws sts get-caller-identity --query Account --output text
```

7. Si se usara SSH, crear una Key Pair EC2 en AWS Console o por CLI:

```powershell
aws ec2 create-key-pair --key-name case-inteligente-ec2 --query "KeyMaterial" --output text > case-inteligente-ec2.pem
```

Si se usara Session Manager, no es obligatorio crear key pair.

## 4. Construir y subir imagen backend a ECR

Desde la raiz del proyecto:

```powershell
cd "D:\NO BORRAR\parcial1"
```

Ejecutar el script de build y push backend:

```powershell
.\scripts\aws-deploy.ps1 -AwsAccountId TU_ACCOUNT_ID -Region us-east-1 -BackendRepository TU_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend -Tag latest
```

La imagen resultante sera:

```text
TU_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend:latest
```

## 5. Configurar Terraform

Entrar a Terraform:

```powershell
cd "D:\NO BORRAR\parcial1\infra\aws\terraform"
```

Copiar variables:

```powershell
Copy-Item .\terraform.tfvars.example .\terraform.tfvars
```

Editar `terraform.tfvars`:

```text
aws_region            = "us-east-1"
project_name          = "case-inteligente"
domain_name           = "tu-dominio.com"
frontend_domain       = "app.tu-dominio.com"
api_domain            = "api.tu-dominio.com"
route53_zone_id       = "ZXXXXXXXXXXXXX"
backend_image         = "TU_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend:latest"
frontend_bucket_name  = "case-inteligente-frontend-tu-dominio"
artifacts_bucket_name = "case-inteligente-artifacts-tu-dominio"
database_name         = "case_inteligente"
database_username     = "case_user"
database_password     = "UNA_CONTRASENA_SEGURA"
jwt_secret_key        = "UN_SECRETO_JWT_LARGO_Y_SEGURO"
ec2_instance_type     = "t3.small"
ec2_key_name          = null
enable_ssh            = false
admin_ssh_cidr        = "TU_IP_PUBLICA/32"
```

Si se usara SSH:

```text
ec2_key_name   = "case-inteligente-ec2"
enable_ssh     = true
admin_ssh_cidr = "TU_IP_PUBLICA/32"
```

## 6. Crear infraestructura AWS EC2

Inicializar Terraform:

```powershell
terraform init
```

Formatear archivos:

```powershell
terraform fmt
```

Validar:

```powershell
terraform validate
```

Revisar plan:

```powershell
terraform plan
```

Aplicar:

```powershell
terraform apply
```

Confirmar con `yes`.

Terraform creara:

- VPC.
- Subnets publicas y privadas.
- Security Groups.
- RDS PostgreSQL.
- S3 de artefactos.
- S3 de frontend.
- CloudFront.
- ACM para API y frontend.
- ALB HTTPS.
- EC2 backend.
- IAM Role para EC2 con permisos ECR, SSM, S3 y CloudWatch.
- Route53 para `api_domain` y `frontend_domain`.

## 7. Esperar arranque de EC2

El arranque puede tardar varios minutos porque EC2:

1. Instala Docker.
2. Instala AWS CLI.
3. Hace login a ECR.
4. Descarga la imagen backend.
5. Ejecuta el contenedor en puerto `8000`.
6. Registra la instancia en el ALB.

Ver outputs:

```powershell
terraform output
```

Verificar salud local desde AWS:

```powershell
$tgArn = terraform output -raw backend_target_group_arn
aws elbv2 describe-target-health --target-group-arn $tgArn --region us-east-1
```

Tambien puedes revisar en AWS Console:

1. EC2.
2. Load Balancers.
3. Target Groups.
4. Target `healthy`.

## 8. Verificar API

Abrir:

```text
https://api.tu-dominio.com/health
```

Debe responder:

```json
{"status":"ok","component":"backend"}
```

Abrir Swagger:

```text
https://api.tu-dominio.com/docs
```

## 9. Desplegar frontend en S3 y CloudFront

Volver a la raiz del proyecto:

```powershell
cd "D:\NO BORRAR\parcial1"
```

Ejecutar despliegue frontend:

```powershell
.\scripts\deploy-frontend-s3.ps1 -Bucket case-inteligente-frontend-tu-dominio -CloudFrontDistributionId DISTRIBUTION_ID -ApiBaseUrl https://api.tu-dominio.com/api/v1 -WsBaseUrl wss://api.tu-dominio.com
```

El `DISTRIBUTION_ID` sale de:

```powershell
cd "D:\NO BORRAR\parcial1\infra\aws\terraform"
terraform output cloudfront_distribution_id
```

## 10. Verificar frontend

Abrir:

```text
https://app.tu-dominio.com
```

Probar:

1. Registro de usuario.
2. Login.
3. Crear proyecto.
4. Crear diagrama.
5. Validar diagrama.
6. Transformar UML.
7. Generar backend.
8. Generar frontend.

## 11. Acceder a EC2 para diagnostico

Recomendado con Session Manager:

```powershell
aws ssm start-session --target ID_DE_LA_INSTANCIA --region us-east-1
```

Dentro de EC2:

```bash
sudo docker ps
```

```bash
sudo docker logs case-inteligente-backend --tail 200
```

```bash
curl http://127.0.0.1:8000/health
```

Si se habilito SSH:

```powershell
ssh -i .\case-inteligente-ec2.pem ec2-user@IP_PUBLICA_EC2
```

## 12. Actualizar backend despues de cambios

Desde la raiz local:

```powershell
.\scripts\aws-deploy.ps1 -AwsAccountId TU_ACCOUNT_ID -Region us-east-1 -BackendRepository TU_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend -Tag latest
```

Reiniciar EC2 para que vuelva a ejecutar user data si cambiaste Terraform:

```powershell
cd "D:\NO BORRAR\parcial1\infra\aws\terraform"
terraform apply
```

Para actualizar solo el contenedor sin recrear infraestructura, entrar por SSM y ejecutar:

```powershell
$instanceId = terraform output -raw backend_ec2_instance_id
cd "D:\NO BORRAR\parcial1"
.\scripts\ec2-refresh-backend.ps1 -InstanceId $instanceId -Region us-east-1 -BackendImage TU_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/case-inteligente-backend:latest
```

## 13. Apagar o destruir infraestructura

Antes de destruir, recuerda que RDS tiene `deletion_protection = true`. Para destruir todo:

1. Cambiar temporalmente `deletion_protection = false` en `aws_db_instance.postgres`.
2. Ejecutar:

```powershell
terraform apply
```

3. Destruir:

```powershell
terraform destroy
```

## 14. Checklist final

- ECR contiene imagen backend.
- Terraform aplica sin errores.
- Target Group del ALB queda `healthy`.
- `https://api.tu-dominio.com/health` responde OK.
- `https://api.tu-dominio.com/docs` abre Swagger.
- Frontend fue subido a S3.
- CloudFront fue invalidado.
- `https://app.tu-dominio.com` abre la plataforma.
- Registro, login y flujo de generacion funcionan.
