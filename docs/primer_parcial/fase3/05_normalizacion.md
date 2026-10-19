# Fase 3 - Normalizacion

## Primera forma normal

Cumplimiento:

- Cada tabla representa una entidad o relacion clara.
- No existen grupos repetitivos dentro de columnas escalares.
- Atributos, metodos y parametros UML se separan en tablas propias.
- Roles y permisos se separan en tablas relacionales.

Uso controlado de `JSONB`:

- Se reserva para metadatos, snapshots, payloads, estilos y manifiestos.
- No reemplaza relaciones criticas del dominio.

## Segunda forma normal

Cumplimiento:

- Las tablas de relacion (`user_roles`, `project_members`, `project_permissions`) tienen claves propias UUID y restricciones unicas sobre combinaciones naturales.
- Los atributos dependen de la entidad completa y no de una parte de una clave compuesta.
- Versiones dependen del proyecto y numero de version mediante restriccion unica.

## Tercera forma normal

Cumplimiento:

- Datos de usuarios no se repiten en proyectos.
- Roles globales se almacenan una sola vez.
- Integrantes separan usuario, proyecto y rol interno.
- Clases UML no duplican datos del diagrama.
- Atributos, metodos y parametros no duplican informacion de clase.
- Artefactos generados referencian generaciones en vez de duplicar informacion.

## Decisiones de desnormalizacion controlada

- `project_versions.snapshot` almacena estado versionado en `JSONB` para recuperacion completa.
- `collaboration_events.payload` almacena el evento original para trazabilidad.
- `ai_processes.input_payload` y `output_payload` preservan la solicitud y respuesta de IA.
- `manifest` en generaciones permite registrar estructura de archivos generada.

Estas decisiones se justifican porque los datos son historicos, variables o de auditoria, y no reemplazan las entidades normalizadas.

