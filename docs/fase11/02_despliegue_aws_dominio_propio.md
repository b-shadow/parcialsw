# Despliegue AWS con Dominio Propio

## Servicios AWS definidos

La infraestructura declarativa esta en `infra/aws/terraform/` e incluye:

- VPC con subnets publicas y privadas.
- Application Load Balancer HTTPS.
- ECS Fargate para backend FastAPI.
- RDS PostgreSQL 16.
- S3 versionado para artefactos generados.
- S3 privado para frontend.
- CloudFront para frontend.
- ACM para certificados TLS.
- Route53 para `app.tu-dominio.com` y `api.tu-dominio.com`.
- CloudWatch Logs para backend.

## Dominio propio

El dominio se parametriza con:

- `domain_name`
- `frontend_domain`
- `api_domain`
- `route53_zone_id`

Ejemplo:

- Frontend: `https://app.tu-dominio.com`
- API: `https://api.tu-dominio.com`
- WebSocket: `wss://api.tu-dominio.com`

## Validacion

La configuracion Terraform fue formateada e inicializada con provider AWS y `terraform validate` finalizo correctamente.
