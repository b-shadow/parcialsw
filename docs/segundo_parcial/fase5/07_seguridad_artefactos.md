# Seguridad y publicacion de artefactos

## Staging atomico

Backend y frontend se generan bajo `.<generation_id>.staging`. Solo despues de preflight, validacion cruzada, escaneo y verificacion se renombra el directorio a su ubicacion definitiva. Ante excepcion, staging se elimina.

## Idempotencia

La tabla `coordinated_generations` define unicidad sobre `transformation_id`, `requested_by_user_id` y `client_request_id`. Repetir una solicitud devuelve el registro existente y evita duplicar trabajo.

## Acceso

Preflight, ejecucion, consulta y descarga exigen usuario autenticado y membresia del proyecto. La operacion queda en bitacora con ID y hash del plan.

## Escaneo

Antes del bundle se recorren fuentes legibles y se excluyen directorios generados de herramientas. Se detectan patrones de claves AWS y asignaciones sospechosas de secretos. No se incluyen variables del entorno de la plataforma.

## Bundle

El ZIP full stack contiene ambos proyectos, `generation-manifest.json` y los planes. ZIP internos y carpetas de build no se duplican en el bundle.

## Migracion

La revision `f6a0b3c4d5e6` agrega estado, etapa, plan, diagnosticos, manifiesto, ruta de artefacto y referencias opcionales a generaciones individuales.
