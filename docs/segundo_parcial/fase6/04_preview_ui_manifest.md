# Preview basado en ui_manifest

## Origen funcional

`build_ui_manifest()` deriva modulos, pantallas, campos, controles y acciones del `GenerationPlan`. El hash fuente es el hash canonico del plan. Se expone mediante `GET /generation/transformations/{id}/ui-manifest` y tambien acompana el preflight coordinado.

Para cada entidad se publican vistas de lista, detalle, formulario y filtro. Las acciones de usuario incluyen interaccion, placement y confirmacion. Un `date` produce `date_picker`; booleanos, numericos y referencias usan sus controles contractuales.

## Render

React permite elegir modulo, pantalla, estado, viewport, modo inspeccionado y escala de texto. Los estados `loading`, `empty`, `error`, `offline`, `unauthorized` y `success` son simulaciones visuales sin invocar el backend generado.

La muestra usa nombres y campos del manifiesto. No existe la antigua entidad fija `Cliente`. Si no hay transformacion se informa que debe transformarse el diagrama, sin inventar estructura funcional.
