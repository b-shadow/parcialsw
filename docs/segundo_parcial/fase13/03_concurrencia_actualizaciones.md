# Concurrencia y actualizaciones

## Revision optimista

`UmlDiagramRepository.replace_if_revision` exige que `revision = expected_revision + 1` y filtra por `_id` y revision observada. Si otro colaborador gano la carrera, no modifica el documento y devuelve `None`.

El bloqueo SQL de `ProjectMutationGuard` serializa las mutaciones de la proyeccion y produce una revision monotona. Los eventos WebSocket existentes conservan `client_event_id`, `base_version`, secuencia y correlacion para deduplicar y detectar clientes atrasados.

## Escritura parcial

El worker compara la revision almacenada con la entrante:

- cambios de una clase o relacion: `$set` sobre `content.classes.$[id]` o `content.relationships.$[id]`;
- atributos, metodos, parametros, especificaciones y visuales: viajan dentro de la clase identificada;
- altas, bajas o reordenamiento canonico: reemplazo del arreglo `classes` o `relationships` solamente;
- importaciones masivas o saltos de revision: reemplazo protegido del agregado.

La revision y el hash se actualizan en la misma operacion atomica. Una revision igual con hash diferente se considera conflicto y va a reintento/dead-letter, nunca se acepta silenciosamente.
