# Fase 8 - Exportacion y versionado de artefactos

## Ubicacion

Los backends generados se escriben en:

```text
storage/generated/backend/{generated_backend_id}/{artifact_id}/
```

## ZIP

Se genera automaticamente:

```text
storage/generated/backend/{generated_backend_id}/{artifact_id}.zip
```

## Registro

La generacion se registra en:

- `generated_backends`
- `generated_artifacts`
- `audit_logs`

## Manifiesto

El manifiesto contiene:

- Tecnologia.
- Lenguaje.
- Base de datos.
- Nombre del proyecto.
- Artifact ID.
- Paquete base.
- Capas generadas.
- Cantidad de entidades.
- Cantidad de relaciones.
- Cantidad de archivos.
- Ruta ZIP.
- Checksums SHA-256 por archivo.

## Descarga

Endpoint:

```text
GET /api/v1/generation/spring-boot/{backend_id}/download
```
