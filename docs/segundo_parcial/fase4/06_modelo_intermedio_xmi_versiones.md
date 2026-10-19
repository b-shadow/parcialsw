# Modelo intermedio, XMI y versiones

## Modelo intermedio v2

Cada metodo exporta:

```json
{
  "id": "uuid",
  "name": "registrar",
  "parameters": [],
  "specification": {},
  "readiness": {
    "status": "ready",
    "ready_for_generation": true,
    "diagnostics": []
  }
}
```

El modelo se genera desde una carga del diagrama y valida todas las especificaciones sin consultas por metodo. Esta decision evita el patron N+1 durante transformaciones grandes.

## Compatibilidad v1

`adapt_intermediate_model_v1_to_v2` realiza copia profunda. Agrega parametros, especificacion nula y readiness `legacy`; nunca modifica el diccionario original. La version 2 pasa sin cambios y las versiones futuras desconocidas se rechazan expresamente.

Los generadores Spring Boot y Flutter llaman `require_supported_intermediate_model` antes de procesar. Por tanto, la frontera de compatibilidad es unica y verificable.

## XMI

La firma se representa con operaciones y parametros UML. La especificacion se incorpora como `TaggedValue` con clave `case_method_specification_v1` y JSON canonico. ElementTree realiza el escape XML.

Durante importacion:

- se recuperan parametros, tipos, valores y orden;
- se limita el tagged value a 64 KiB;
- se exige objeto JSON y `schema_version=1`;
- Pydantic valida el contenido antes de persistir;
- extensiones desconocidas o malformadas se ignoran sin romper el XMI base.

## Snapshots

El constructor interno de diagramas incluye especificacion y revision. Por ello los snapshots V2 y las versiones guardadas conservan el contrato. `readiness` es derivado y no se persiste como columna ni se pasa al constructor ORM durante restauracion.

## Migracion

`e5f9a2b3c4d5_phase4_method_specification_revision.py` agrega `revision` con valor inicial uno y restriccion positiva. El downgrade elimina restriccion y columna. La migracion depende de la migracion de contratos de fase 1.

