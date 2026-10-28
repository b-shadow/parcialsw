# Modelo documental activo

## Documento

```json
{
  "_id": "diagram-uuid",
  "project_id": "project-uuid",
  "schema_version": 1,
  "revision": 24,
  "content": {
    "id": "diagram-uuid",
    "project_id": "project-uuid",
    "name": "Sistema academico",
    "classes": [],
    "relationships": [],
    "metadata_json": {}
  },
  "content_hash": "sha256",
  "created_at": "UTC",
  "updated_at": "UTC"
}
```

Cada clase incluye atributos, metodos, parametros, especificacion funcional, metadatos y posicion visual. Las relaciones conservan origen, destino, tipo, direccion, etiqueta, multiplicidades y metadatos de clase asociativa.

## Invariantes

- `_id` coincide con `content.id`.
- `project_id` coincide con `content.project_id`.
- Las relaciones solo referencian clases del mismo agregado.
- El hash se calcula sobre contenido canonico ordenado.
- Una revision no puede disminuir ni reutilizarse con contenido diferente.
- Existe un unico documento activo por proyecto.

## Indices

- `_id`: identificador compartido con `uml_diagrams.id`.
- `uq_uml_diagrams_project`: unicidad por `project_id`.
- `ix_uml_diagrams_updated`: operacion y diagnostico temporal.
- SQL `ix_uml_diagrams_updated_id`: cursor estable para migracion por lotes.
