# Modelo documental de versiones

## Coleccion

`uml_diagram_versions` contiene un documento por version. Las versiones nunca se incrustan en el diagrama activo.

```json
{
  "_id": "uuid-version",
  "schema_version": 1,
  "project_id": "uuid-proyecto",
  "diagram_id": "uuid-diagrama",
  "version_number": 4,
  "project_revision": 18,
  "snapshot_schema_version": 2,
  "name": "Entrega estable",
  "description": "Antes del cambio",
  "kind": "manual",
  "snapshot_size_bytes": 18240,
  "content": {"schema_version": 2, "project": {}, "diagrams": []},
  "content_hash": "sha256",
  "created_by_user_id": "uuid-usuario",
  "created_at": "UTC",
  "updated_at": "UTC"
}
```

`content` conserva clases, atributos, metodos, especificaciones, parametros, relaciones, multiplicidades, posiciones, tema y configuracion no sensible del proyecto.

## Indices

- unico `(diagram_id, version_number)`;
- unico `(project_id, version_number)`;
- consulta `(project_id, created_at desc)`;
- diagnostico por `content_hash`.

El validador Mongo exige UUID, fechas, revision, esquema, tipo de version, contenido y SHA-256.
