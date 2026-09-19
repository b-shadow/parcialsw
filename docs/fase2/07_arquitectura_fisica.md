# Fase 2 - Arquitectura fisica

## Entorno local de desarrollo

Componentes:

- Navegador web.
- Frontend Vite en `127.0.0.1:5173`.
- Backend FastAPI en `127.0.0.1:8000`.
- PostgreSQL Docker en `localhost:5433`.
- Motor IA local como proceso o servicio independiente.
- Generadores como modulos invocados por backend.

## Entorno productivo esperado

Componentes:

- Cliente web desde navegador.
- CDN/hosting estatico para frontend.
- Servicio backend FastAPI.
- PostgreSQL administrado.
- Almacenamiento de archivos.
- Servicio de IA local/offline en infraestructura controlada.
- Workers de generacion para tareas pesadas.
- Monitoreo y logs.

## AWS candidata

| Necesidad | Servicio candidato |
| --- | --- |
| Hosting frontend | S3 + CloudFront o Amplify |
| Backend FastAPI | EC2 o ECS |
| Base de datos | RDS PostgreSQL |
| Archivos generados/XMI | S3 |
| Balanceo | Application Load Balancer |
| Seguridad de red | VPC, subnets, security groups |
| Logs y metricas | CloudWatch |
| CI/CD | GitHub Actions o CodePipeline |

## Comunicacion

- Frontend a backend: HTTPS REST.
- Frontend a colaboracion: WSS.
- Backend a PostgreSQL: conexion privada.
- Backend a IA: HTTP/local RPC o llamada de proceso local segun despliegue.
- Backend a generadores: servicio interno o modulo de aplicacion.
- Backend a S3: SDK autorizado para artefactos.

## Consideraciones

- La IA debe poder operar sin llamadas a servicios externos.
- Los artefactos generados deben almacenarse con control de acceso.
- WebSockets requieren balanceo compatible con sesiones persistentes o broker futuro.
- Las tareas largas de generacion deben ejecutarse asincronamente en fases posteriores.

