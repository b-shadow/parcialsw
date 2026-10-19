# Preflight y diagnosticos

## Flujo

El endpoint `POST /api/v1/generation/coordinated/preflight` compila el plan sin crear directorios ni registros de artefactos. Devuelve `ready`, `canonical_hash`, diagnosticos y el plan inspeccionable.

## Bloqueos implementados

- Metodo en `draft`, `invalid`, `legacy` o sin `ready_for_generation`.
- Nombre reservado o colision normalizada.
- Tipo, control o entidad referenciada desconocidos.
- Operacion `custom` sin estrategia ejecutable.
- Operacion expuesta sin contrato backend.
- Accion de usuario sin contrato Flutter.
- Parametro de ruta ausente.
- GET con efecto mutante.
- Ruta duplicada o colision con CRUD.
- Regla de error sin bloque `generation` soportado.
- Regla de unicidad o calculo sin campos.
- Campo Flutter que no corresponde a la firma.

## Diagnostico accionable

Cada item contiene `code`, `severity`, `message`, `suggestion`, `method_id`, `class_id` y `path`. La interfaz presenta estos datos antes de habilitar el boton de generacion.

## Garantia

`ensure_plan_ready` se ejecuta antes de crear el directorio de staging. Una precondicion invalida no deja ZIP parcial ni carpeta publicada.
