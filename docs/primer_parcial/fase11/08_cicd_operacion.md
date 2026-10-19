# CI/CD y Operacion

## GitHub Actions

Se agrego `.github/workflows/ci-cd.yml`.

El pipeline ejecuta:

- lint y tests de `ai-engine`.
- lint y tests de backend.
- lint, tests y build de frontend.
- build Docker de backend.
- build frontend React para S3/CloudFront.
- build Docker de ai-engine.

## Scripts operativos

- `scripts/aws-deploy.ps1`: build y push de imagen backend a ECR para EC2.
- `scripts/ec2-refresh-backend.ps1`: actualizacion del contenedor backend en EC2 mediante SSM.
- `scripts/deploy-frontend-s3.ps1`: build frontend, sync a S3 e invalidacion CloudFront.
- `scripts/docker-prod-smoke.ps1`: build y smoke test local de compose productivo.
- `scripts/smoke-test.ps1`: validacion HTTP del sistema.

## Flujo productivo

1. Validar pruebas.
2. Construir imagen backend.
3. Publicar imagen backend a ECR.
4. Aplicar Terraform.
5. Publicar frontend a S3.
6. Ejecutar smoke test contra dominios HTTPS.
