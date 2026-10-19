# Fase 8 - Integracion FastAPI y frontend

## Backend

`GenerationService.generate_backend` ahora:

- Lee la transformacion UML.
- Ejecuta el generador Spring Boot.
- Escribe archivos.
- Crea ZIP.
- Registra artefactos.
- Actualiza manifiesto.

## Frontend

La vista `GenerationPage` muestra:

- Estado de transformacion.
- Backend Spring Boot generado.
- Cantidad de archivos.
- Cantidad de entidades.
- Descarga ZIP usando Axios con JWT.

## Separacion arquitectonica

El backend FastAPI principal no es reemplazado ni mezclado con el backend generado. El generador crea un proyecto Spring Boot independiente.
