# Arquitectura funcional

## Responsabilidades

| Dato | Autoridad en Fase 12 |
|---|---|
| Proyecto, propietario y permisos | PostgreSQL |
| Registro de version, numero, autor, revision y estado | PostgreSQL |
| Snapshot UML completo e inmutable | MongoDB |
| JSONB historico | PostgreSQL, solo rollback temporal |
| Diagrama editable | PostgreSQL hasta la Fase 13 |

El acceso siempre se autoriza en PostgreSQL antes de consultar MongoDB. No existen uniones entre motores: `ProjectService` compone el registro relacional con el documento identificado por el mismo UUID.

## Flujo

```text
guardar version
  -> construir ProjectSnapshotV2
  -> insertar ProjectVersion + evento Outbox en una transaccion SQL
  -> worker valida contrato
  -> insertar documento inmutable en uml_diagram_versions

vista previa/restaurar
  -> validar proyecto y rol en SQL
  -> obtener registro ProjectVersion
  -> leer documento Mongo por _id
  -> comprobar proyecto, numero y hash
  -> usar fallback SQL solo si la politica lo permite
```

El contrato HTTP no expone el snapshot. El frontend conserva sus tipos y rutas actuales.
