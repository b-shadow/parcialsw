# Arquitectura funcional

## Autoridad de datos

| Responsabilidad | Autoridad |
|---|---|
| Proyecto, propietario, miembros y permisos | PostgreSQL |
| Registro del diagrama y revision del proyecto | PostgreSQL |
| Contenido UML activo | MongoDB, con fallback SQL temporal |
| Proyeccion relacional editable durante fase 13 | PostgreSQL |
| Entrega entre almacenes | Outbox transaccional |

La API valida primero proyecto y membresia en PostgreSQL. Luego `ActiveUmlDocumentStore` obtiene el agregado de `uml_diagrams` en MongoDB. Si el documento falta, es invalido, Mongo no esta disponible o su revision esta por detras de una escritura pendiente, puede leer la proyeccion SQL segun las banderas de rollback.

## Flujo de escritura

1. El servicio bloquea el proyecto y aumenta `projects.revision`.
2. La mutacion actualiza la proyeccion relacional dentro de la misma transaccion.
3. El listener `before_commit` serializa el agregado completo y agrega un evento Outbox en esa transaccion.
4. El worker valida identidad y referencias, y aplica el cambio solo si la revision no retrocede.
5. Para revisiones consecutivas usa `$set` y `arrayFilters` por ID; ante cambios estructurales reemplaza solo el arreglo afectado.

Este diseno conserva permisos y atomicidad SQL mientras la fase 14 prepara el retiro de las tablas de contenido.
