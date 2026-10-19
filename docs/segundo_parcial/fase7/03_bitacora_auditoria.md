# Bitacora y auditoria

## Actividad del proyecto

`CollaborationEvent` incorpora recurso, correlacion, causalidad y clave de resumen. Los aliases historicos como `CREATE_CLASS` se escriben en taxonomia canonica como `UML_CLASS_CREATED`.

La consulta vigente es:

```http
GET /api/v1/projects/{project_id}/activity?before_sequence=351&limit=50&type=PROJECT_VERSION_RESTORED
```

El cursor es `sequence_number`, el orden es descendente y las inserciones nuevas no desplazan paginas anteriores. `/{project_id}/changes` se mantiene por compatibilidad.

## Auditoria

La auditoria administrativa permanece separada. `sanitize_audit_metadata()` elimina passwords, tokens, autorizaciones, secretos, claves, datos Web Push, cookies y conexiones; tambien limita profundidad, colecciones y textos.

Una restauracion no elimina actividad, auditoria, generaciones ni mensajes de IA. El contenido puede retroceder; la trazabilidad solo avanza.

