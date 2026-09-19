# Integracion FastAPI y Frontend

## Backend FastAPI

Se actualizo `GenerationService.generate_frontend` para generar artefactos reales con `FlutterGeneratorService`.

Se agrego acceso a frontend generado en `GenerationRepository.get_frontend`.

Se agrego endpoint de descarga:

`GET /api/v1/generation/flutter/{frontend_id}/download`

El endpoint valida autenticacion, membresia del proyecto y existencia del ZIP antes de responder con `FileResponse`.

## Frontend React

Se actualizo el modulo de transformacion y generacion para:

- llamar a `/generation/flutter`.
- descargar ZIP desde `/generation/flutter/{frontend_id}/download`.
- mostrar cantidad de archivos y entidades generadas.
- mantener la relacion opcional con un backend Spring Boot generado.

## Compatibilidad

La integracion mantiene el contrato de fase 8 para Spring Boot y extiende el flujo full stack sin cambiar los endpoints existentes.
