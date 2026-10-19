# Almacenamiento, Backups y Artefactos

## Artefactos

Los proyectos generados Spring Boot y Flutter se registran en base de datos y se almacenan localmente en despliegue Docker o en S3 para produccion AWS.

## S3

Terraform define bucket de artefactos con:

- versionado.
- cifrado SSE-S3.
- bloqueo de acceso publico.

## Backups

Se agregaron scripts:

- `scripts/backup-postgres.ps1`
- `scripts/restore-postgres.ps1`

RDS se configura con:

- almacenamiento cifrado.
- retencion de backups de 7 dias.
- proteccion contra eliminacion.
- snapshot final obligatorio.

## Recuperacion

La restauracion se realiza desde dump PostgreSQL o snapshots RDS segun el tipo de incidente.
