# Plan de migracion NoSQL desde la Fase 10

## 1. Objetivo

Incorporar MongoDB como almacenamiento documental de CASE Inteligente sin reemplazar las responsabilidades transaccionales de PostgreSQL. La migracion comenzara en la Fase 10 y se ejecutara de forma incremental, medible y reversible.

La arquitectura objetivo sera hibrida:

- PostgreSQL conservara usuarios, autenticacion, roles, proyectos, miembros, permisos, metadatos de diagramas, generaciones, notificaciones y auditoria critica.
- MongoDB almacenara el contenido completo de los diagramas UML, sus snapshots documentales, conversaciones, mensajes y contexto extenso de IA.
- Los UUID generados por la aplicacion relacionaran ambos almacenes.
- PostgreSQL seguira siendo la autoridad para comprobar existencia, propiedad y acceso a un proyecto.

## 2. Distribucion objetivo de datos

| Informacion | Almacen principal | Relacion |
|---|---|---|
| Usuarios, sesiones y roles | PostgreSQL | Claves foraneas SQL |
| Proyectos, miembros y permisos | PostgreSQL | `projects.id` |
| Registro y revision del diagrama | PostgreSQL | `uml_diagrams.id`, `project_id` |
| Clases, atributos, metodos y relaciones UML | MongoDB | `_id = uml_diagrams.id` |
| Posiciones y configuracion visual UML | MongoDB | Incluidas en el documento UML |
| Versiones completas del diagrama | MongoDB | `diagram_id`, `project_id`, `version_number` |
| Conversaciones | PostgreSQL inicialmente; registro minimo SQL al finalizar | `conversation_id`, `project_id` |
| Mensajes y contexto extenso de IA | MongoDB | `conversation_id`, `project_id` |
| Generaciones Spring Boot y Flutter | PostgreSQL | `project_id`, `diagram_id`, `source_revision` |
| Archivos generados | Almacen de artefactos | Referencia persistida en PostgreSQL |

## 3. Reglas de arquitectura

1. El mismo UUID identificara una entidad compartida en PostgreSQL y MongoDB.
2. No se realizaran uniones directas entre bases; los servicios de aplicacion compondran las respuestas.
3. Toda lectura de MongoDB estara precedida por la validacion de acceso al proyecto en PostgreSQL.
4. El contenido UML tendra una sola fuente de verdad durante la operacion normal.
5. La escritura doble solo se utilizara temporalmente durante una migracion controlada.
6. Cada documento UML tendra `schema_version`, `revision`, `content_hash`, `created_at` y `updated_at`.
7. Los mensajes y versiones seran documentos independientes; no se usaran arreglos que crezcan sin limite.
8. Los archivos, imagenes originales y ZIP no se almacenaran dentro de documentos BSON.
9. Las operaciones entre almacenes utilizaran Outbox, reintentos idempotentes y tareas de reconciliacion.
10. Cada fase debera incluir rollback, metricas, pruebas y verificacion de datos antes de retirar estructuras existentes.

## 4. Fase 10: base MongoDB, contratos y observabilidad

### Objetivo

Preparar la infraestructura NoSQL y los contratos compartidos sin cambiar todavia la fuente de verdad funcional.

### Trabajo

- Incorporar MongoDB al entorno local, pruebas, CI y despliegue.
- Integrar el controlador oficial PyMongo Async con el ciclo de vida de FastAPI.
- Definir variables `MONGODB_URI`, `MONGODB_DATABASE` y limites de tiempo de conexion.
- Agregar health checks separados para PostgreSQL y MongoDB.
- Crear modulos de conexion, repositorios y manejo de errores NoSQL.
- Definir esquemas versionados para diagramas, versiones, conversaciones y mensajes.
- Crear indices unicos y compuestos antes de migrar datos.
- Definir el contrato de UUID compartido y fechas UTC.
- Implementar Outbox y operaciones idempotentes para sincronizacion entre almacenes.
- Crear herramientas de conteo, comparacion de hashes y deteccion de documentos huerfanos.

### Colecciones iniciales

```text
uml_diagrams
uml_diagram_versions
ai_messages
ai_context_snapshots
migration_checkpoints
```

### Criterios de cierre

- MongoDB inicia localmente y en CI.
- FastAPI informa la salud de ambos almacenes.
- Los indices y validadores se crean de forma idempotente.
- Ningun flujo existente cambia su comportamiento.
- Las pruebas de conexion, timeout, reconexion y configuracion quedan aprobadas.

## 5. Fase 11: conversaciones y memoria de IA en MongoDB

**Estado: completada.** Detalle y evidencia en `docs/segundo_parcial/fase11/`.

### Objetivo

Migrar primero la informacion de crecimiento no acotado y menor dependencia relacional: mensajes, referencias y contexto de IA.

### Trabajo

- Mantener en PostgreSQL el registro de conversacion, su proyecto, autor, titulo, estado y secuencias.
- Guardar cada mensaje como documento independiente en `ai_messages`.
- Conservar `conversation_id`, `project_id`, `sequence_number`, rol, autor, contenido, referencias, intenciones y metadatos.
- Crear indice unico por `(conversation_id, sequence_number)`.
- Crear indice idempotente para `client_message_id` cuando exista.
- Migrar los mensajes existentes por lotes con checkpoints reiniciables.
- Habilitar lectura comparada y, temporalmente, escritura doble.
- Cambiar la lectura principal a MongoDB cuando los conteos, secuencias y hashes coincidan.
- Mantener resumenes de conversacion y contexto del modelo como documentos separados.

### Criterios de cierre

- No se pierden autores, orden, referencias ni estados de mensajes.
- La paginacion hacia adelante y atras conserva el contrato actual.
- Una reconexion WebSocket no duplica mensajes.
- Los chats extensos no cargan todo el historial en memoria.
- Existe rollback de lectura a PostgreSQL durante el periodo de estabilizacion.

## 6. Fase 12: snapshots y versiones UML documentales

**Estado: completada.** Detalle y evidencia en `docs/segundo_parcial/fase12/`.

### Objetivo

Validar el modelo documental con copias inmutables del diagrama antes de mover el contenido editable.

### Trabajo

- Guardar cada version UML como un documento independiente en `uml_diagram_versions`.
- Incluir clases, atributos, metodos, especificaciones, relaciones, multiplicidades y datos visuales.
- Conservar `project_id`, `diagram_id`, `version_number`, `project_revision`, autor y hash.
- Migrar los snapshots JSONB existentes por lotes.
- Comparar restauraciones SQL y MongoDB sobre los mismos casos de prueba.
- Cambiar guardado, vista previa y restauracion para utilizar el snapshot documental.
- Impedir que las versiones se incrusten como arreglo dentro del diagrama activo.
- Definir politica de retencion y respaldo sin borrar versiones manuales validas.

### Criterios de cierre

- Un snapshot exportado desde ambos almacenes produce el mismo modelo canonico.
- Guardar y restaurar versiones mantiene referencias y especificaciones de metodos.
- Las versiones son inmutables y tienen hash verificable.
- La restauracion crea respaldo previo y es idempotente.
- Se prueba compatibilidad con snapshots de esquemas anteriores.

## 7. Fase 13: contenido UML activo en MongoDB

**Estado: completada.** Detalle y evidencia en `docs/segundo_parcial/fase13/`.

### Objetivo

Convertir el documento MongoDB en la fuente de verdad del contenido editable del unico diagrama de cada proyecto.

### Modelo objetivo

```json
{
  "_id": "uuid-del-diagrama",
  "project_id": "uuid-del-proyecto",
  "schema_version": 1,
  "revision": 24,
  "classes": [],
  "relationships": [],
  "visual": {},
  "content_hash": "sha256",
  "created_at": "UTC",
  "updated_at": "UTC"
}
```

### Trabajo

- Mantener en PostgreSQL `uml_diagrams` como registro, relacion con proyecto y control operativo.
- Migrar clases, atributos, metodos, parametros, especificaciones y relaciones al documento MongoDB.
- Implementar un repositorio UML documental detras de la interfaz de servicio existente.
- Aplicar reemplazo atomico del agregado validado con hash y revision; optimizar a actualizaciones parciales solo si la medicion demuestra que es necesario.
- Implementar concurrencia optimista mediante `expected_revision` y aumento atomico de `revision`.
- Validar en la aplicacion que cada relacion apunte a clases existentes en el mismo documento.
- Adaptar importacion XMI, lectura de imagen, IA, validacion, exportacion y generadores al modelo canonico.
- Mantener eventos WebSocket con revision, correlacion e idempotencia.
- Ejecutar escritura doble temporal y comparar hashes antes del cambio definitivo.
- Activar MongoDB como fuente principal mediante una bandera de caracteristica reversible.

### Criterios de cierre

- Crear, editar, mover y eliminar elementos conserva el comportamiento actual.
- Dos colaboradores reciben conflictos controlados o cambios combinables sin perder informacion.
- Importar y exportar XMI mantiene todas las relaciones soportadas.
- La generacion Spring Boot y Flutter utiliza la revision UML correcta.
- Los hashes SQL y MongoDB coincidieron durante la ventana de comparacion previa.
- El rollback posterior al retiro fisico se realiza restaurando el backup coordinado.

## 8. Fase 14: consolidacion, retiro SQL y endurecimiento

**Estado: completada.** Detalle y evidencia en `docs/segundo_parcial/fase14/`.

### Objetivo

Eliminar la duplicacion temporal cuando MongoDB haya demostrado estabilidad y completar la operacion hibrida.

### Trabajo

- Detener la escritura doble despues de una ventana definida sin divergencias.
- Conservar respaldo exportable de las tablas UML y mensajes SQL antes de retirarlas.
- Eliminar gradualmente tablas de contenido UML y mensajes que ya no sean fuente de verdad.
- Mantener tablas de registro SQL necesarias para permisos, navegacion y trazabilidad.
- Crear tareas periodicas de reconciliacion de referencias PostgreSQL-MongoDB.
- Detectar proyectos, diagramas, conversaciones y mensajes huerfanos.
- Probar respaldo y restauracion coordinados de ambos almacenes.
- Medir latencia, tamano de documentos, contencion por revision y consumo de indices.
- Definir alertas para conexiones, replicas, errores de Outbox y diferencias de hash.
- Actualizar diagramas de arquitectura, manuales de despliegue y matriz de trazabilidad.

### Criterios de cierre

- No existen lecturas funcionales dependientes de las tablas retiradas.
- No existen documentos huerfanos ni referencias invalidas conocidas.
- Los respaldos coordinados pueden restaurarse en un entorno limpio.
- Las pruebas backend, frontend, WebSocket, IA, XMI y generadores quedan aprobadas.
- La documentacion identifica claramente la fuente de verdad de cada dato.

## 9. Orden de migracion

```text
Fase 10: infraestructura y contratos
    -> Fase 11: mensajes y contexto de IA
    -> Fase 12: snapshots y versiones UML
    -> Fase 13: contenido UML editable
    -> Fase 14: retiro SQL y endurecimiento
```

Este orden reduce el riesgo: primero se migra informacion documental de crecimiento alto, luego datos UML inmutables y, solo despues de validar ambos casos, el estado colaborativo editable.

## 10. Condiciones para iniciar cada fase

- La fase anterior debe tener pruebas reproducibles y acta de cierre.
- Debe existir una estrategia de rollback probada.
- Los contratos publicos no pueden cambiar sin versionado o compatibilidad temporal.
- No se eliminara informacion SQL mientras exista alguna divergencia pendiente.
- Toda migracion masiva debe ser reiniciable, observable e idempotente.
- Los datos sensibles se sanearan antes de almacenarse en contexto o mensajes de IA.

## 11. Resultado final esperado

CASE Inteligente operara con persistencia poliglota: PostgreSQL asegurara identidad, permisos, relaciones administrativas y operaciones transaccionales; MongoDB representara de forma natural el diagrama UML completo, sus versiones y la memoria extensa del asistente. La aplicacion conservara los contratos actuales y podra evolucionar el modelo documental sin convertir cada cambio visual o de IA en una migracion relacional.
