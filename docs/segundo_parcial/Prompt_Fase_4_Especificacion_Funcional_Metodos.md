# PROMPT FASE 4: ESPECIFICACION FUNCIONAL DE METODOS UML

## 0. Instruccion maestra

Implementar la Fase 4 de la segunda parte de CASE Inteligente: transformar cada metodo UML que represente comportamiento funcional en una especificacion estructurada, validada, persistente y suficientemente precisa para que, en la Fase 5, los generadores Spring Boot y Flutter produzcan comportamiento coherente desde una sola fuente de verdad.

La implementacion debe ampliar el sistema existente. No debe crear un editor UML paralelo, un segundo modelo intermedio ni contratos separados e incompatibles para backend y frontend.

La fase debe utilizar:

- Los contratos, entidades y migraciones definidos en la Fase 1.
- El motor unico de IA, Ollama/Qwen, fallback y salida estructurada de la Fase 2.
- La conversacion compartida, identidad, acciones confirmables y sincronizacion de la Fase 3.
- El modelo UML, editor, validacion, XMI, versiones, auditoria y WebSocket existentes.
- Los transformadores actuales que producen el modelo intermedio para Spring Boot y Flutter.

La IA puede proponer, completar y refinar una especificacion. El backend conserva la autoridad para validar referencias, tipos, permisos, rutas, parametros y consistencia. Ninguna salida del modelo se persiste directamente sin validacion.

---

## 1. Objetivo funcional

Al finalizar la fase:

1. Un metodo conserva su firma UML basica: nombre, visibilidad, retorno y parametros.
2. El mismo metodo puede tener una especificacion funcional uno a uno.
3. La especificacion describe que hace, bajo que condiciones y para quien se expone.
4. Todas las referencias apuntan a elementos reales del mismo diagrama.
5. La IA puede completar campos desde lenguaje natural sin inventar elementos.
6. El usuario puede revisar y corregir cada campo antes de aplicarlo.
7. El sistema distingue borrador, advertencias y preparacion para generar.
8. Guardar y volver a abrir mantiene todos los datos.
9. Importar, exportar y versionar conserva la informacion cuando el formato lo permite.
10. El modelo intermedio incluye una representacion versionada y comun para ambos generadores.
11. Los metodos antiguos sin especificacion siguen abriendo y generando con el comportamiento previo.
12. La Fase 5 puede consumir el contrato sin reinterpretar texto libre.

---

## 2. Alineacion obligatoria entre fases

### Dependencias de Fase 1

Reutilizar, no duplicar:

- `UmlMethodSpecification`.
- Tabla `uml_method_specifications`.
- Relacion uno a uno con `UmlMethod`.
- Campos JSONB estructurados.
- `schema_version`.
- Contratos de snapshot y modelo intermedio versionados.
- Convenciones UTC, UUID, auditoria e idempotencia.

### Dependencias de Fase 2

Reutilizar:

- Orquestador unico de IA.
- `OllamaProvider` y `RuleEngineProvider`.
- Clasificacion multiintencion.
- Contexto autorizado.
- Salida JSON validada por Pydantic/JSON Schema.
- Politica de riesgo y confirmacion.
- Fallback cuando Ollama no esta disponible.

### Dependencias de Fase 3

Reutilizar:

- Conversacion unica por proyecto.
- Autor autenticado.
- `correlation_id` y `client_message_id`.
- Acciones propuestas, confirmadas, rechazadas y aplicadas.
- Publicacion WebSocket posterior al commit.
- Deduplificacion en frontend.

### Entrega hacia Fase 5

La Fase 4 entrega:

- Especificacion efectiva validada.
- Estado de preparacion por metodo.
- Contrato backend normalizado.
- Contrato Flutter normalizado.
- Referencias resueltas mediante IDs estables.
- Modelo intermedio `schema_version` conocido.
- Diagnosticos que impiden o permiten generar.

La Fase 5 sera responsable de convertir esos contratos en codigo Spring Boot y Flutter. No adelantar en esta fase plantillas completas de controladores, servicios, widgets o pantallas.

---

## 3. Precondiciones

Antes de implementar, comprobar:

- La migracion de Fase 1 existe y puede subir y bajar.
- `UmlMethodSpecification` esta registrado en SQLAlchemy.
- La relacion con `UmlMethod` usa `ON DELETE CASCADE`.
- La API puede cargar metodos con parametros.
- El modelo interno puede representar metodos y parametros.
- El endpoint de interaccion IA de Fase 2 funciona con proveedor simulado.
- El proyecto activo y diagrama activo forman parte del contexto de Fase 3.
- El WebSocket rechaza usuarios sin membresia.
- El guardado manual de versiones existente captura el diagrama.

Si una precondicion perteneciente a una fase anterior falta, completarla respetando el prompt propietario. No crear una solucion temporal incompatible dentro de esta fase.

---

## 4. Alcance exacto

- Edicion completa de firma y especificacion funcional.
- CRUD de parametros que falte en la API/UI.
- Clasificacion del tipo de operacion.
- Definicion de exposicion `internal`, `api` o `user_action`.
- Condiciones, reglas, validaciones, efectos y permisos.
- Referencias a entidades, atributos, relaciones y parametros.
- Contrato backend declarativo.
- Contrato Flutter declarativo.
- Refinamiento asistido por IA.
- Validacion determinista y diagnosticos accionables.
- Estado de completitud para generacion.
- Persistencia, carga y actualizacion atomica.
- Integracion colaborativa y auditoria.
- Integracion con modelo intermedio.
- Conservacion en snapshots y XMI mediante extensiones compatibles.
- Pruebas unitarias, integracion, frontend y regresion.
- Documentacion tecnica y funcional.

---

## 5. Fuera de alcance

- Generar implementaciones Spring Boot finales.
- Generar widgets Flutter finales.
- Ejecutar automaticamente logica de negocio descrita.
- Crear entidades UML inexistentes sin una accion UML separada y confirmada.
- Entrenar Qwen.
- Convertir texto libre en codigo arbitrario.
- Permitir scripts, SQL o expresiones ejecutables en reglas.
- Redisenar el editor de estilos de la Fase 6.
- Cambiar el modelo de versionado global de la Fase 7.
- Implementar la PWA movil reducida de la Fase 8.

---

## 6. Herramientas y tecnologias

### Backend

- Python y FastAPI.
- SQLAlchemy 2.
- PostgreSQL y JSONB.
- Alembic.
- Pydantic 2 para DTO y validacion.
- Servicios existentes de UML, proyectos, permisos, auditoria e IA.
- `pytest` para pruebas unitarias e integracion.
- Cliente de prueba FastAPI para REST.

### Inteligencia artificial

- Orquestador de Fase 2.
- Ollama con modelo Qwen configurable.
- JSON Schema derivado de modelos Pydantic.
- Proveedor de reglas para inferencias simples y fallback.
- Presupuesto de contexto y limites de reparacion ya definidos.

### Frontend

- React, TypeScript y Vite.
- Servicios HTTP existentes.
- Store y cliente WebSocket de Fase 3.
- Componentes compartidos existentes.
- Lucide para iconos.
- Vitest y React Testing Library.

### Intercambio

- Modelo intermedio JSON versionado.
- XMI/XML mediante `ElementTree` y el importador/exportador existentes.
- Tagged values o extension propia con namespace estable cuando XMI no represente el campo de forma nativa.

No introducir otra libreria de formularios, validacion o estado si el repositorio ya tiene una solucion suficiente.

---

## 7. Linea base y brecha actual

La implementacion actual contiene:

- `UmlMethod` con nombre, retorno, visibilidad, orden y `metadata_json`.
- `UmlParameter` con nombre, tipo, valor por defecto y orden.
- Creacion, actualizacion y eliminacion de metodos.
- Creacion de parametros.
- Modelo interno `UmlMethodModel`.
- Editor tabular basico de nombre y retorno.
- Transformacion que solo copia nombre, retorno y visibilidad.
- Generadores que todavia ignoran la semantica de los metodos.

La brecha de esta fase es convertir la firma tecnica en un contrato funcional explicito. No almacenar toda la nueva informacion de manera opaca dentro de `metadata_json` si Fase 1 ya definio la entidad normalizada.

---

## 8. Fuente unica de verdad

La fuente autoritativa se divide asi:

- `uml_methods`: firma UML.
- `uml_parameters`: parametros ordenados.
- `uml_method_specifications`: semantica funcional.
- Clases, atributos y relaciones del diagrama: referencias validas.
- Roles y permisos del proyecto: autorizacion para editar la especificacion.

`backend_contract` y `frontend_contract` son dos vistas coordinadas de la misma operacion. No deben contener reglas contradictorias ni repetir toda la especificacion.

El frontend nunca decide por si solo que una referencia existe o que una especificacion esta lista. Puede mostrar validacion inmediata, pero el estado definitivo proviene del backend.

---

## 9. Modelo de dominio

Usar la entidad de Fase 1 con estos campos:

```text
id                      UUID PK
method_id               UUID UNIQUE FK -> uml_methods.id ON DELETE CASCADE
description             TEXT NULL
operation_kind          VARCHAR(40) NOT NULL DEFAULT 'custom'
exposure                VARCHAR(30) NOT NULL DEFAULT 'internal'
preconditions           JSONB NOT NULL DEFAULT []
postconditions          JSONB NOT NULL DEFAULT []
business_rules          JSONB NOT NULL DEFAULT []
validations             JSONB NOT NULL DEFAULT []
side_effects            JSONB NOT NULL DEFAULT []
required_permissions    JSONB NOT NULL DEFAULT []
related_entities        JSONB NOT NULL DEFAULT []
backend_contract        JSONB NOT NULL DEFAULT {}
frontend_contract       JSONB NOT NULL DEFAULT {}
schema_version          INTEGER NOT NULL DEFAULT 1
revision                INTEGER NOT NULL DEFAULT 1
created_at              TIMESTAMPTZ NOT NULL
updated_at              TIMESTAMPTZ NOT NULL
```

Si Fase 1 ya creo la tabla sin `revision`, agregar una migracion incremental de Fase 4 con valor inicial `1`. Incrementar `revision` atomicamente en cada mutacion. Agregar indices solo si una consulta real los necesita. No indexar indiscriminadamente todos los JSONB.

---

## 10. Firma UML y parametros

La firma es independiente de la especificacion:

```text
+ inscribir(estudianteId: UUID, cursoId: UUID, fecha: Date): Inscripcion
```

Reglas:

- Nombre obligatorio y valido para generacion.
- Nombre unico por clase considerando firma, segun la politica existente.
- Tipo de retorno normalizado pero conservando el valor UML original cuando sea necesario.
- Parametros con nombres unicos sin distinguir mayusculas.
- `order_index` estable y sin duplicados efectivos.
- Tipos primitivos conocidos o referencia a clase del mismo diagrama.
- Valor por defecto compatible con el tipo.
- No crear un metodo visual fantasma cuando la lista esta vacia.
- Una clase puede no tener metodos.

Completar endpoints de parametros si faltan:

```text
POST   /api/v1/uml/methods/{method_id}/parameters
PATCH  /api/v1/uml/parameters/{parameter_id}
DELETE /api/v1/uml/parameters/{parameter_id}
```

Toda operacion debe verificar acceso a traves del metodo, clase, diagrama y proyecto.

---

## 11. Enumeracion `operation_kind`

Valores permitidos:

- `create`: crea una entidad o recurso.
- `read`: obtiene un recurso por identificador.
- `search`: lista, filtra o busca recursos.
- `update`: modifica un recurso existente.
- `delete`: elimina o desactiva un recurso.
- `calculate`: calcula y devuelve un resultado sin representar CRUD por si mismo.
- `business_action`: ejecuta una accion de dominio, por ejemplo aprobar, inscribir o cerrar.
- `custom`: no puede clasificarse de forma segura en las categorias anteriores.

No inferir solo por una palabra aislada. Considerar nombre, descripcion, clase propietaria, parametros, retorno, reglas y entidades relacionadas.

---

## 12. Enumeracion `exposure`

- `internal`: operacion usada dentro del backend; no exige endpoint ni control Flutter.
- `api`: operacion expuesta por endpoint; puede ser consumida por otra integracion sin accion visual directa.
- `user_action`: operacion visible para el usuario; exige contrato backend y evaluacion Flutter.

Reglas:

- Metodo UML `private` no puede exponerse como `api` o `user_action` sin diagnostico de error.
- `user_action` requiere etiqueta e interaccion Flutter valida.
- `api` y `user_action` requieren metodo HTTP y ruta.
- `internal` debe tener contratos vacios o campos compatibles con uso interno.
- Cambiar exposicion no elimina datos silenciosamente; advertir y permitir limpieza explicita.

---

## 13. Estructura comun de reglas

Precondiciones, postcondiciones, reglas y validaciones deben usar objetos, no cadenas ambiguas:

```json
{
  "code": "student_must_exist",
  "description": "El estudiante debe existir",
  "severity": "error",
  "target": {
    "kind": "parameter",
    "id": "uuid-del-parametro",
    "name": "estudianteId"
  },
  "error_code": "STUDENT_NOT_FOUND",
  "generation": null
}
```

Campos:

- `code`: `snake_case`, unico dentro de la coleccion.
- `description`: texto humano breve y obligatorio.
- `severity`: `info`, `warning` o `error`.
- `target`: opcional, referencia estructurada.
- `error_code`: opcional, `UPPER_SNAKE_CASE`.
- `generation`: bloque estructurado opcional para reglas que deban convertirse en codigo durante la Fase 5. Nunca contiene codigo libre.

Normalizar cadenas heredadas a objetos durante lectura/escritura controlada. No ejecutar expresiones contenidas en estos campos.

Cuando una regla deba ser generable, `generation` usa un catalogo cerrado compartido con la Fase 5. Ejemplo:

```json
{
  "kind": "unique_by_fields",
  "entity_id": "uuid-inscripcion",
  "fields": ["estudianteId", "cursoId"]
}
```

La Fase 4 valida forma, referencias y operandos. La Fase 5 compila solamente clases de regla soportadas. Una descripcion sin operandos puede guardarse como borrador, pero no debe considerarse suficiente para generacion semantica.

---

## 14. Precondiciones y postcondiciones

### Precondiciones

Describen lo que debe cumplirse antes:

- Recurso existente.
- Estado permitido.
- Parametro presente.
- Usuario autorizado.
- Ausencia de duplicados.

### Postcondiciones

Describen resultados observables:

- Entidad creada.
- Estado actualizado.
- Relacion persistida.
- Resultado calculado.
- Coleccion sin cambios si falla una validacion.

No confundir postcondiciones con mensajes de interfaz ni con detalles de implementacion Java/Dart.

---

## 15. Reglas de negocio y validaciones

Separar:

- Regla de negocio: restriccion del dominio, por ejemplo no duplicar una inscripcion activa.
- Validacion de entrada: formato, rango, obligatoriedad o longitud.
- Precondicion: estado necesario antes de operar.
- Permiso: capacidad requerida del actor.

Ejemplos:

```json
{
  "code": "grade_range",
  "description": "La nota final debe estar entre 0 y 100",
  "severity": "error",
  "target": {"kind": "attribute", "id": "uuid", "name": "notaFinal"},
  "error_code": "INVALID_FINAL_GRADE"
}
```

No aceptar reglas que nombren elementos inexistentes sin marcarlas como no resueltas.

---

## 16. Efectos secundarios

Estructura:

```json
{
  "code": "refresh_enrollment_list",
  "kind": "data_change",
  "description": "Crea una inscripcion y actualiza la lista",
  "target_entity_id": "uuid-de-inscripcion",
  "target_entity_name": "Inscripcion"
}
```

Tipos iniciales:

- `data_change`.
- `status_change`.
- `notification`.
- `audit_event`.
- `refresh_required`.

No permitir efectos `execute_script`, SQL libre ni URL arbitraria.

---

## 17. Permisos requeridos

Formato:

```json
{
  "code": "enrollment.create",
  "description": "Permite registrar inscripciones"
}
```

Reglas:

- Codigo estable con formato `recurso.accion`.
- No convertir automaticamente roles de proyecto en permisos del sistema generado.
- Diferenciar permiso para editar el UML del permiso que tendra la aplicacion generada.
- La IA puede sugerir un permiso, pero debe marcarlo como propuesta.
- La lista final debe ser explicita y sin duplicados.

---

## 18. Entidades relacionadas

Formato canonico:

```json
{
  "class_id": "uuid",
  "class_name": "Estudiante",
  "relation": "input_reference",
  "required": true,
  "source_parameter_id": "uuid-del-parametro"
}
```

Relaciones permitidas inicialmente:

- `owner`.
- `input_reference`.
- `output`.
- `reads`.
- `creates`.
- `updates`.
- `deletes`.
- `refresh_target`.

`class_id` es autoritativo. `class_name` es una instantanea legible. Si cambia el nombre de clase, sincronizar el nombre mostrado conservando el ID.

---

## 19. Resolucion de referencias

Resolver en este orden:

1. ID explicito valido.
2. Nombre exacto sin distinguir mayusculas.
3. Alias unico normalizado.
4. Coincidencia contextual unica en clase propietaria y relaciones.
5. Solicitar aclaracion.

Nunca seleccionar silenciosamente entre varias coincidencias.

Validar que:

- La clase pertenece al mismo diagrama.
- El atributo pertenece a la clase referenciada.
- El parametro pertenece al metodo.
- La relacion UML existe si la regla afirma navegar por ella.
- Una entidad asociativa referencia los extremos reales.
- El tipo del parametro es compatible con la referencia.

---

## 20. Contrato backend

Formato canonico version 1:

```json
{
  "http_method": "POST",
  "path": "/inscripciones",
  "request_dto": "CrearInscripcionRequest",
  "response_dto": "InscripcionResponse",
  "transactional": true,
  "authorization": ["enrollment.create"],
  "error_codes": ["STUDENT_NOT_FOUND", "COURSE_NOT_FOUND", "DUPLICATE_ENROLLMENT"],
  "status_codes": {
    "success": 201,
    "validation_error": 400,
    "not_found": 404,
    "conflict": 409
  }
}
```

Validaciones:

- `http_method`: `GET`, `POST`, `PUT`, `PATCH` o `DELETE`.
- `path`: inicia con `/`, no contiene host, query fija ni `..`.
- Parametros `{id}` de ruta existen en la firma o son resolubles por contexto.
- GET no declara cuerpo mutante.
- `request_dto` es opcional cuando no hay entrada.
- `response_dto` coincide con retorno o salida declarada.
- `transactional` recomendado para escrituras.
- Codigos de error unicos y normalizados.
- Codigos HTTP validos y coherentes con la operacion.

Esta fase define el contrato; no genera todavia el controlador final.

---

## 21. Contrato Flutter

Formato canonico version 1:

```json
{
  "interaction": "form",
  "label": "Inscribir estudiante",
  "placement": "list_primary_action",
  "confirmation_required": false,
  "refresh_targets": ["uuid-de-inscripcion"],
  "success_message": "Inscripcion registrada",
  "fields": [
    {
      "parameter_id": "uuid-estudiante-id",
      "parameter": "estudianteId",
      "control": "entity_selector",
      "source_entity_id": "uuid-estudiante",
      "source_entity": "Estudiante",
      "display_fields": ["id", "nombre"],
      "required": true
    },
    {
      "parameter_id": "uuid-fecha",
      "parameter": "fecha",
      "control": "date_picker",
      "required": true
    }
  ]
}
```

Interacciones iniciales:

- `form`.
- `button`.
- `filter`.
- `detail_action`.
- `list_action`.
- `none`.

Controles iniciales:

- `text_input`.
- `multiline_text`.
- `number_input`.
- `decimal_input`.
- `date_picker`.
- `date_time_picker`.
- `switch`.
- `entity_selector`.
- `single_select`.
- `multi_select`.
- `hidden_context`.

No definir colores ni tipografia aqui; pertenecen al tema de Fase 6.

---

## 22. Mapeo de tipos a controles

Reglas deterministas iniciales:

| Tipo UML | Control sugerido |
| --- | --- |
| `String`, `char`, `text` | `text_input` |
| Texto largo segun descripcion | `multiline_text` |
| `Integer`, `Long` | `number_input` |
| `Double`, `Float`, `Decimal` | `decimal_input` |
| `Boolean` | `switch` |
| `Date` | `date_picker` |
| `DateTime` | `date_time_picker` |
| UUID que referencia clase | `entity_selector` |
| Enum o conjunto cerrado | `single_select` |
| Coleccion de referencias | `multi_select` |

La inferencia se puede editar. Un UUID sin referencia conocida no se convierte automaticamente en selector de entidad.

---

## 23. Coherencia backend-frontend

Validar conjuntamente:

- Cada campo Flutter referencia un parametro real.
- Cada parametro visible tiene un control o una razon para ser contexto oculto.
- `entity_selector` referencia una clase real.
- `display_fields` existen en la clase fuente.
- La ruta y metodo HTTP existen en contrato backend.
- La accion visible no apunta a una operacion `internal`.
- `refresh_targets` referencia entidades reales.
- Mensajes no contienen secretos ni HTML ejecutable.
- Confirmacion visual es obligatoria para eliminaciones o acciones destructivas.
- Errores backend tienen una estrategia de presentacion generica en Flutter.

Esta coherencia debe estar centralizada en un validador compartido del backend, no duplicada de manera divergente entre generadores.

---

## 24. Estados de completitud

Calcular, no almacenar como verdad mutable salvo necesidad justificada:

- `empty`: no existe especificacion o esta vacia.
- `draft`: contiene informacion parcial.
- `needs_review`: fue propuesta/refinada por IA y espera revision.
- `invalid`: contiene errores bloqueantes.
- `ready`: cumple requisitos para su exposicion.
- `legacy`: metodo sin especificacion que usara compatibilidad anterior.

Respuesta de validacion:

```json
{
  "status": "draft",
  "ready_for_generation": false,
  "errors": [],
  "warnings": [
    {
      "code": "missing_flutter_contract",
      "path": "frontend_contract",
      "message": "La accion visible necesita representacion Flutter"
    }
  ],
  "inferred_fields": ["operation_kind"]
}
```

---

## 25. Niveles de validacion

### Validacion de borrador

- Permite guardar informacion incompleta.
- Rechaza estructura corrupta, IDs ajenos y valores inseguros.
- Devuelve advertencias de completitud.

### Validacion estricta

- Se usa al marcar listo o transformar para generacion semantica.
- Exige contratos segun exposicion.
- Exige referencias resueltas.
- Bloquea contradicciones.

### Validacion de compatibilidad

- Metodos antiguos sin especificacion no bloquean el flujo previo.
- Si el usuario comienza una especificacion, se valida como borrador.
- Si declara `user_action`, no puede degradarse silenciosamente a CRUD heredado.

---

## 26. Diagnosticos

Cada diagnostico debe incluir:

```json
{
  "code": "unknown_related_entity",
  "severity": "error",
  "path": "related_entities[1].class_id",
  "message": "La clase Curso indicada no pertenece al diagrama",
  "suggestion": "Seleccione una clase existente",
  "related_element_id": "uuid-opcional"
}
```

Reglas:

- Mensajes claros en espanol.
- Codigos estables para frontend y pruebas.
- Ruta precisa al campo.
- No devolver trazas internas.
- Errores bloquean `ready`; advertencias no necesariamente.
- Evitar recomendaciones genericas que no indiquen el campo afectado.

---

## 27. API REST

Implementar o completar:

```text
GET    /api/v1/uml/methods/{method_id}/specification
PUT    /api/v1/uml/methods/{method_id}/specification
PATCH  /api/v1/uml/methods/{method_id}/specification
DELETE /api/v1/uml/methods/{method_id}/specification
POST   /api/v1/uml/methods/{method_id}/specification/validate
POST   /api/v1/uml/methods/{method_id}/specification/refine
```

Decisiones:

- `GET` responde `200` con un sobre que contiene `specification: null` y `readiness.status: legacy` cuando el metodo existe pero aun no tiene especificacion. `404` se reserva para metodo inexistente o no visible.
- `PUT` reemplaza toda la especificacion con control de concurrencia.
- `PATCH` modifica campos presentes, no convierte ausentes en vacios.
- `DELETE` elimina la semantica, no el metodo UML.
- `validate` no muta.
- `refine` produce propuesta; no aplica sin confirmacion cuando modifica datos persistidos.

`GET`, `PUT` y `PATCH` devuelven `ETag: "revision-{n}"`. `PUT`, `PATCH` y `DELETE` exigen `If-Match` con la revision observada; crear por primera vez usa `If-None-Match: *`. Ejecutar la comparacion y el incremento en la misma sentencia/transaccion. Responder `409 Conflict` con la revision actual y sin sobrescribir ante una revision obsoleta. `refine` recibe `base_revision`, pero no muta hasta que su accion se confirma contra esa misma revision.

---

## 28. DTO Pydantic

Crear tipos explicitos:

- `MethodRuleItem`.
- `MethodTargetReference`.
- `MethodSideEffect`.
- `RequiredPermission`.
- `RelatedEntityReference`.
- `BackendMethodContract`.
- `BackendStatusCodes`.
- `FlutterMethodContract`.
- `FlutterFieldContract`.
- `MethodSpecificationCreate`.
- `MethodSpecificationUpdate`.
- `MethodSpecificationResponse`.
- `MethodSpecificationValidationResponse`.
- `MethodSpecificationRefineRequest`.
- `MethodSpecificationProposalResponse`.

Configurar:

- Longitudes maximas.
- Cantidades maximas por lista.
- `extra="forbid"` en contratos controlados.
- Enums o `Literal`.
- Normalizacion antes de persistir.
- Serializacion estable.

No usar `dict` sin forma en los limites API solo porque la columna es JSONB.

---

## 29. Servicio de aplicacion

Crear un servicio cohesivo, por ejemplo `MethodSpecificationService`, responsable de:

1. Cargar metodo, clase, diagrama y proyecto.
2. Verificar membresia y rol.
3. Cargar contexto UML necesario.
4. Normalizar DTO.
5. Resolver referencias.
6. Validar reglas internas y cruzadas.
7. Verificar revision esperada.
8. Persistir en una transaccion.
9. Registrar auditoria.
10. Confirmar commit.
11. Publicar evento colaborativo.

Los routers no deben contener reglas de negocio. El repositorio no decide permisos ni semantica.

---

## 30. Permisos de edicion

Aplicar los roles reales del proyecto:

- Miembro con permiso de edicion UML: crea y modifica especificaciones.
- Usuario de solo lectura: consulta especificacion y diagnosticos.
- Creador u organizador: no obtiene reglas especiales salvo las ya definidas por la plataforma.
- Usuario sin membresia: no descubre si el metodo existe.

Refinar con IA requiere acceso de lectura. Aplicar la propuesta requiere acceso de edicion y, si corresponde, confirmacion.

No confiar en `project_id`, `role` o `user_id` enviados por el cliente.

---

## 31. Flujo de edicion manual

1. Usuario selecciona una clase.
2. Abre la especificacion de un metodo real.
3. Frontend solicita detalle y catalogo de referencias del diagrama.
4. Usuario edita firma o semantica.
5. Frontend valida formato local basico.
6. Backend valida borrador completo.
7. Si existen errores estructurales, no persiste.
8. Si hay advertencias, persiste como borrador.
9. Backend audita y emite evento tras commit.
10. Otros colaboradores actualizan el mismo metodo sin duplicarlo.

No guardar automaticamente cada pulsacion. Usar borrador local y comando claro de guardado.

---

## 32. Flujo de refinamiento con IA

1. Usuario abre un metodo del diagrama activo.
2. Escribe o dicta una descripcion funcional.
3. Frontend envia `method_id`, instruccion, revision base y `client_message_id`.
4. Backend resuelve proyecto y diagrama desde el metodo.
5. Construye contexto autorizado y acotado.
6. Incluye firma, clase, atributos, relaciones y especificacion actual.
7. Orquestador clasifica `refine_method_specification`.
8. Qwen o fallback devuelve un parche estructurado.
9. Backend valida JSON Schema.
10. Resuelve referencias por ID.
11. Devuelve propuesta, diferencias y diagnosticos.
12. La propuesta aparece en la conversacion compartida de Fase 3.
13. Usuario autorizado confirma, corrige o rechaza.
14. Al confirmar, backend revalida revision y permisos.
15. Persiste una sola vez y publica evento posterior al commit.

No aplicar automaticamente una propuesta que cambie exposicion, permisos, referencias o reglas.

---

## 33. Contrato de salida de IA

La IA debe responder una estructura similar a:

```json
{
  "method_id": "uuid",
  "base_revision": 4,
  "summary": "Completa la operacion de inscripcion",
  "patch": {
    "description": "Registra un estudiante en un curso",
    "operation_kind": "business_action",
    "exposure": "user_action",
    "preconditions": [],
    "postconditions": [],
    "business_rules": [],
    "validations": [],
    "side_effects": [],
    "required_permissions": [],
    "related_entities": [],
    "backend_contract": {},
    "frontend_contract": {}
  },
  "unresolved_references": [],
  "assumptions": [],
  "warnings": []
}
```

Reglas:

- `method_id` debe coincidir con el solicitado.
- El modelo no elige IDs inexistentes.
- Toda suposicion queda explicita.
- Una referencia ambigua va en `unresolved_references`.
- El backend ignora campos extra.
- Un parche invalido se repara dentro del limite de Fase 2 o usa fallback seguro.

---

## 34. Inferencia determinista

Aplicar reglas seguras antes o despues de IA:

- `crear`, `registrar`, `agregar` suelen sugerir `create`.
- `obtener`, `consultar detalle` sugieren `read`.
- `listar`, `buscar`, `filtrar` sugieren `search`.
- `actualizar`, `editar`, `cambiar` sugieren `update`.
- `eliminar`, `borrar`, `desactivar` sugieren `delete` segun semantica.
- `calcular`, `totalizar`, `promediar` sugieren `calculate`.
- Verbos de dominio como aprobar, inscribir o cerrar sugieren `business_action`.

Estas son sugerencias, no decisiones basadas solo en palabras. Si nombre y descripcion se contradicen, emitir advertencia o pedir aclaracion.

---

## 35. Lenguaje natural que debe comprender

Ejemplos:

### Creacion funcional

> El metodo inscribir recibe estudianteId, cursoId y fecha. Debe comprobar que ambos existan, evitar una inscripcion repetida y devolver la inscripcion creada. El usuario lo ejecuta desde un formulario.

Debe proponer:

- `business_action` o `create` justificado.
- Entidades Estudiante, Curso e Inscripcion existentes.
- Precondiciones de existencia.
- Regla de duplicado.
- Endpoint POST.
- Selectores de Estudiante y Curso.
- Selector de fecha.
- Refresco de Inscripcion.

### Consulta

> buscarDisponibles permite filtrar cursos por nombre y duracion, se muestra como filtro en la lista.

Debe proponer `search`, GET, query parameters y contrato Flutter `filter`.

### Metodo interno

> calcularTotal suma los importes y solo lo usa el servicio al guardar una venta.

Debe proponer `calculate`, `internal` y sin boton Flutter.

### Solicitud compuesta

> Completa registrarPago y aprobarSolicitud; el primero usa un formulario y el segundo pide confirmacion.

Debe producir dos acciones independientes, cada una ligada a su `method_id`, con confirmacion separada y aplicacion atomica por metodo, no una escritura parcial opaca.

---

## 36. Manejo de ambiguedad

Solicitar aclaracion cuando:

- Existen dos clases con nombre equivalente.
- No se sabe si un ID referencia entidad o valor simple.
- La ruta propuesta colisiona con otra operacion incompatible.
- El metodo dice eliminar pero la descripcion dice desactivar.
- No se identifica el resultado esperado.
- El usuario pide una accion visible sin indicar donde y no existe una inferencia segura.
- Una regla depende de un atributo inexistente.

No bloquear por detalles visuales opcionales. Diferenciar una duda bloqueante de una recomendacion editable.

---

## 37. Editor frontend

Ampliar el editor de propiedades del metodo mediante un panel o modal de trabajo, no agregando decenas de columnas a la tabla compacta.

Estructura recomendada:

- Encabezado con clase, firma, estado y cierre.
- Pestana `Firma`.
- Pestana `Comportamiento`.
- Pestana `Backend`.
- Pestana `Flutter`.
- Pestana `Validacion`.

La tabla de metodos conserva acciones breves:

- Editar especificacion.
- Guardar firma.
- Eliminar.
- Indicador de estado.

No anidar tarjetas decorativas. Usar secciones, tablas y formularios densos coherentes con el editor existente.

---

## 38. Pestana Firma

Incluir:

- Nombre.
- Visibilidad.
- Tipo de retorno.
- Lista ordenable de parametros.
- Nombre, tipo, valor por defecto y orden de cada parametro.
- Agregar, editar y eliminar parametros.

Requisitos:

- Controles estables sin saltos de layout.
- Confirmar eliminacion si el parametro esta referenciado en contratos.
- Mostrar donde se usa antes de eliminar.
- Reordenar de forma accesible, con botones si drag-and-drop no es accesible.
- Guardar firma y especificacion de manera coherente.

---

## 39. Pestana Comportamiento

Incluir:

- Descripcion funcional.
- Tipo de operacion.
- Exposicion.
- Precondiciones.
- Postcondiciones.
- Reglas de negocio.
- Validaciones.
- Efectos secundarios.
- Permisos.
- Entidades relacionadas.

Usar editores de listas estructuradas. No pedir al usuario editar JSON crudo como flujo principal.

Cada fila debe permitir agregar, editar, quitar y mostrar diagnosticos del campo.

---

## 40. Pestana Backend

Incluir:

- Metodo HTTP mediante menu.
- Ruta.
- DTO de entrada.
- DTO de respuesta.
- Transaccion mediante toggle.
- Autorizaciones.
- Codigos de error.
- Codigos HTTP.

Mostrar una previsualizacion declarativa, no codigo Java final.

Ocultar o deshabilitar campos no aplicables a `internal`, conservando datos solo si el usuario decide no limpiarlos.

---

## 41. Pestana Flutter

Incluir:

- Tipo de interaccion.
- Etiqueta visible.
- Ubicacion.
- Confirmacion.
- Mensaje de exito.
- Objetivos de refresco.
- Tabla parametro-control.
- Entidad fuente y campos visibles para selectores.

Mostrar controles reales como selector de fecha, booleano o entidad en una previsualizacion compacta opcional. La previsualizacion completa y estilos pertenecen a Fase 6.

No permitir configurar frontend para un metodo `internal` sin advertencia.

---

## 42. Asistencia IA en el editor

Agregar un comando claro como `Refinar con IA` con icono apropiado.

La interfaz debe:

- Aceptar texto y, si la plataforma ya lo soporta, voz convertida a texto.
- Mostrar que metodo sera modificado.
- Mostrar diferencias campo por campo.
- Distinguir valor actual, propuesta y diagnostico.
- Permitir aceptar campos individuales o toda la propuesta.
- Exigir confirmacion antes de persistir.
- Informar proveedor efectivo y fallback sin tecnicismos excesivos.
- Mantener la propuesta si existe un conflicto de revision para que el usuario pueda reintentar.

La IA actua dentro del mismo diagrama donde esta el usuario. No crea un diagrama nuevo.

---

## 43. Estado frontend y concurrencia

Mantener separados:

- Datos confirmados por servidor.
- Borrador local.
- Propuesta IA.
- Diagnosticos.
- Estado de guardado.
- Revision base.

Ante evento WebSocket del mismo metodo:

- Si no hay cambios locales, actualizar.
- Si hay borrador local, informar conflicto y ofrecer recargar o comparar.
- No sobrescribir silenciosamente.
- Deduplificar por `event_id`.
- No aplicar optimistamente como confirmado antes de respuesta REST.

---

## 44. Eventos colaborativos

Extender el protocolo de Fase 3 sin romper eventos existentes:

- `METHOD_SIGNATURE_UPDATED`.
- `METHOD_SPECIFICATION_CREATED`.
- `METHOD_SPECIFICATION_UPDATED`.
- `METHOD_SPECIFICATION_DELETED`.
- `METHOD_SPECIFICATION_REFINED`.

Payload minimo:

```json
{
  "event_id": "uuid",
  "project_id": "uuid",
  "diagram_id": "uuid",
  "class_id": "uuid",
  "method_id": "uuid",
  "actor": {"user_id": "uuid", "display_name": "Usuario"},
  "revision": 5,
  "changed_fields": ["business_rules", "frontend_contract"],
  "occurred_at": "ISO-8601"
}
```

Persistir/auditar antes de emitir. No enviar la especificacion completa si el cliente puede recargarla de forma autorizada.

---

## 45. Auditoria

Registrar:

- Creacion de especificacion.
- Cambio de firma.
- Cambio de exposicion.
- Refinamiento solicitado.
- Propuesta aceptada o rechazada.
- Eliminacion de especificacion.

Metadata segura:

- Proyecto, diagrama, clase y metodo.
- Campos modificados.
- Proveedor IA y fallback.
- `correlation_id`.
- Revision anterior y nueva.

No guardar prompts completos ni datos sensibles indiscriminadamente en la bitacora.

---

## 46. Integracion con la conversacion IA

Cuando el refinamiento nace del chat colaborativo:

- La solicitud aparece como mensaje del usuario.
- La IA responde con resumen y propuesta.
- La propuesta se representa como `AiAction` ligada a `method_id`.
- Todos los miembros pueden verla.
- Solo usuarios con permiso pueden confirmarla.
- La aplicacion exitosa actualiza estado de accion y metodo.
- Un rechazo no altera el metodo.
- Repetir la confirmacion no duplica cambios.

La conversacion documenta la decision, pero no reemplaza la especificacion persistida.

---

## 47. Modelo intermedio

Extender la transformacion existente:

```json
{
  "schema_version": 2,
  "classes": [
    {
      "id": "uuid",
      "name": "Inscripcion",
      "methods": [
        {
          "id": "uuid",
          "name": "inscribir",
          "visibility": "public",
          "return_type": "Inscripcion",
          "parameters": [],
          "specification": {
            "schema_version": 1,
            "operation_kind": "business_action",
            "exposure": "user_action",
            "description": "Registra un estudiante",
            "preconditions": [],
            "postconditions": [],
            "business_rules": [],
            "validations": [],
            "side_effects": [],
            "required_permissions": [],
            "related_entities": [],
            "backend_contract": {},
            "frontend_contract": {}
          },
          "readiness": {
            "status": "ready",
            "ready_for_generation": true,
            "diagnostics": []
          }
        }
      ]
    }
  ]
}
```

Requisitos:

- Incluir parametros, actualmente omitidos por la transformacion.
- Incluir especificacion si existe.
- Incluir estado calculado.
- Mantener IDs estables.
- Copiar una instantanea inmutable al crear `UmlTransformation`.
- No consultar luego datos vivos para alterar una transformacion ya creada.

---

## 48. Compatibilidad del modelo intermedio

- Lectores aceptan version anterior sin `specification`.
- Metodos sin especificacion mantienen comportamiento legacy.
- Version nueva distingue campo ausente de contrato vacio.
- No cambiar nombres existentes de clases, atributos o relaciones.
- Agregar un adaptador explicito `v1 -> v2` si los consumidores lo requieren.
- Rechazar versiones futuras desconocidas con mensaje claro.

La Fase 5 debe poder diferenciar `legacy`, `draft`, `invalid` y `ready`.

---

## 49. Integracion XMI

Conservar de forma nativa:

- Nombre.
- Visibilidad.
- Retorno.
- Parametros.

Para semantica extendida:

- Usar tagged values o extension namespaced estable.
- Serializar JSON canonico o campos separados con version.
- Escapar XML correctamente.
- Imponer limites de tamano.
- Ignorar extensiones desconocidas sin romper importacion.
- Validar el contenido antes de persistir.
- Mantener compatibilidad con Enterprise Architect en la medida real soportada.

Ejemplo conceptual:

```xml
<case:methodSpecification schemaVersion="1">
  <case:description>Registra un estudiante</case:description>
  <case:operationKind>business_action</case:operationKind>
  <case:exposure>user_action</case:exposure>
</case:methodSpecification>
```

No afirmar interoperabilidad total de campos propietarios si la herramienta externa los descarta.

---

## 50. Versiones y snapshots

El snapshot del diagrama debe incluir:

- Firma de metodos.
- Parametros.
- Especificaciones completas.
- `schema_version`.
- Referencias por IDs.

Al restaurar:

- Restaurar especificaciones junto al UML.
- Validar referencias restauradas.
- Conservar la conversacion IA fuera del snapshot, segun Fase 7.
- Crear nuevos registros o reconciliar IDs de acuerdo con el contrato de snapshot de Fase 1.
- No dejar especificaciones huerfanas.

Esta fase prepara el contenido; el endurecimiento completo de restauracion pertenece a Fase 7.

---

## 51. Notificaciones

No enviar push por cada cambio de campo.

Eventos candidatos:

- Propuesta IA lista para revision asignada.
- Conflicto o invalidacion causada por un cambio UML relevante.

Preferir actualizacion WebSocket dentro de la sesion. Usar notificacion persistente/push solo cuando aporta valor y excluir al actor cuando ya conoce el resultado.

---

## 52. Seguridad

- Autor derivado del JWT.
- Verificacion de membresia en cada endpoint.
- Proteccion contra IDOR recorriendo metodo -> clase -> diagrama -> proyecto.
- Limites para descripcion y listas.
- Rechazo de HTML/script no permitido.
- Rutas backend sanitizadas.
- Prohibicion de URL externas en contratos.
- Sin SQL, Java, Dart o plantillas ejecutables en JSONB.
- Salida IA tratada como no confiable.
- Logs sin contenido completo sensible.
- Rate limit para refinamiento IA.
- Idempotencia en solicitud y aplicacion de propuestas.

---

## 53. Rendimiento

- Cargar especificaciones con estrategia ORM que evite N+1.
- No cargar todo el proyecto para editar un metodo si basta un contexto acotado.
- Para validacion de diagrama, precargar clases, atributos, relaciones, metodos y parametros en pocas consultas.
- Limitar listas y longitud de texto.
- No llamar Ollama durante una lectura normal.
- Cachear solo catalogos inmutables o facilmente invalidables.
- Medir tiempo de validacion e inferencia.

---

## 54. Manejo de errores

Casos:

- `404`: recurso inexistente o no visible.
- `409`: revision obsoleta, ruta duplicada o conflicto semantico.
- `422`: estructura o referencia invalida.
- `429`: limite de refinamiento.
- `503`: proveedor IA no disponible sin fallback suficiente.

Una falla de IA no borra el borrador ni altera la especificacion existente. Una falla de publicacion WebSocket posterior al commit no revierte datos confirmados; el cliente los recupera por REST/catch-up.

---

## 55. Observabilidad

Registrar de forma estructurada:

- `project_id`.
- `diagram_id`.
- `class_id`.
- `method_id`.
- `correlation_id`.
- Operacion.
- Revision.
- Estado de validacion.
- Cantidad de errores y advertencias.
- Proveedor IA y fallback.
- Duracion de validacion y refinamiento.

No registrar especificaciones completas por defecto.

Metricas sugeridas:

- Refinamientos solicitados/completados/fallidos.
- Propuestas aceptadas/rechazadas.
- Conflictos de revision.
- Metodos por estado de completitud.
- Errores por codigo de diagnostico.

---

## 56. Pruebas unitarias backend

Cubrir al menos:

- Enums aceptados y rechazados.
- Normalizacion de reglas simples.
- Codigos `snake_case`.
- Codigos de error `UPPER_SNAKE_CASE`.
- Ruta segura.
- Coherencia HTTP/operacion.
- Firma con parametros duplicados.
- Valores por defecto por tipo.
- Resolucion por ID.
- Resolucion unica por nombre.
- Ambiguedad detectada.
- Clase ajena rechazada.
- Atributo inexistente rechazado.
- Selector de entidad valido.
- `display_fields` validos.
- Metodo interno sin Flutter.
- Accion visible sin Flutter.
- Eliminacion con confirmacion.
- Estado `draft`, `invalid`, `ready` y `legacy`.
- Adaptacion de modelo intermedio v1 a v2.
- Salida IA invalida.
- Fallback determinista.

---

## 57. Pruebas de servicio/API

Cubrir:

- Crear especificacion.
- Obtener especificacion.
- Reemplazar con `PUT`.
- Parchear un campo sin borrar los demas.
- Eliminar especificacion sin eliminar metodo.
- Validar sin mutar.
- Validacion estricta devuelve `ready` para un contrato valido.
- Validacion estricta devuelve `invalid` para un contrato incompleto o contradictorio.
- Usuario lector no edita.
- Usuario ajeno no accede.
- Revision obsoleta produce 409.
- Dos solicitudes idempotentes aplican una vez.
- Auditoria se crea.
- Evento se emite despues del commit.
- Rollback no emite evento.
- Borrar metodo elimina especificacion por cascada.

---

## 58. Pruebas de IA

Usar proveedor simulado en suite normal:

- Descripcion completa produce propuesta valida.
- Descripcion parcial conserva campos no solicitados.
- Multiples metodos producen acciones independientes.
- Referencia ambigua queda sin resolver.
- Entidad inventada es rechazada.
- ID inventado es rechazado.
- JSON con campos extra es rechazado o normalizado segun contrato.
- Qwen no disponible usa fallback cuando sea posible.
- Fallback insuficiente devuelve propuesta parcial honesta.
- Confirmacion repetida no duplica cambios.
- La propuesta se liga al diagrama activo real.

Prueba opcional con Ollama real, marcada y omitible. La suite ordinaria no depende de un modelo instalado.

---

## 59. Pruebas frontend

Cubrir:

- Abrir especificacion desde metodo seleccionado.
- Mostrar firma y parametros.
- Agregar, editar, reordenar y eliminar parametro.
- Renderizar cada seccion.
- Cambiar exposicion adapta campos visibles.
- Diagnostico se muestra junto al campo.
- Guardado mantiene borrador ante error.
- Propuesta IA muestra diferencias.
- Aceptar campos seleccionados.
- Rechazar propuesta sin mutar.
- Conflicto WebSocket no pisa borrador.
- Lector ve campos deshabilitados.
- Texto largo no desborda.
- Panel funciona en escritorio y ancho reducido razonable.
- Navegacion por teclado y etiquetas accesibles.

---

## 60. Pruebas de modelo intermedio y XMI

### Modelo intermedio

- Parametros conservan orden.
- Especificacion se copia completa.
- IDs se mantienen.
- Estado se calcula.
- Transformacion creada no cambia al editar luego el UML.
- V1 sigue aceptado.

### XMI

- Exportar e importar conserva firma.
- Extension propia conserva especificacion en round-trip CASE.
- XML sin extension importa normalmente.
- Extension desconocida no rompe.
- XML malicioso o excesivo es rechazado por protecciones existentes.
- Referencias inexistentes importadas quedan diagnosticadas, no conectadas arbitrariamente.

---

## 61. Casos de aceptacion funcional

### Inscripcion completa

En un diagrama con Estudiante, Curso e Inscripcion, crear `inscribir(estudianteId, cursoId, fecha)`. Refinar desde lenguaje natural. Debe obtener contratos coherentes, selectores de entidad y fecha, y quedar `ready` tras revision.

### Metodo interno

`calcularNotaFinal()` se marca `internal`. Debe poder estar listo sin endpoint ni control Flutter.

### Referencia inexistente

Una regla menciona Profesor sin existir esa clase. Debe mostrar error y no marcar listo.

### Ambiguedad

Existen dos clases con nombres equivalentes. La IA debe pedir aclaracion, no elegir una.

### Edicion concurrente

Dos usuarios abren la misma revision. El primero guarda. El segundo recibe conflicto y puede comparar sin perder su borrador.

### Solicitud multiple

El usuario pide completar tres metodos. Se crean tres propuestas identificables; confirmar una no aplica las otras.

### Persistencia

Guardar, cerrar y reabrir. Firma, reglas, contratos y estado deben coincidir.

### Compatibilidad legacy

Un diagrama anterior sin especificaciones abre, valida y transforma sin regresion.

---

## 62. Criterios de aceptacion tecnicos

- No existen `dict` sin validar en limites REST nuevos.
- No hay N+1 evidente al transformar un diagrama.
- No se emiten eventos antes del commit.
- No se aplican propuestas sin revision/permisos.
- No se inventan IDs.
- No se pierde informacion al hacer PATCH.
- La migracion es reversible.
- `git diff --check` no reporta errores nuevos.
- Backend pasa lint/pruebas configuradas.
- Frontend pasa typecheck/pruebas/build.
- Round-trip XMI esta cubierto.
- Modelo intermedio versionado esta cubierto.

---

## 63. Compatibilidad y no regresion

Verificar expresamente:

- Clases sin metodos siguen validas.
- Metodos sin parametros siguen validos.
- No reaparece un metodo visual ficticio.
- Edicion UML manual sigue funcionando sin IA.
- Texto, voz e imagen siguen creando firmas basicas.
- Importacion/exportacion anterior sigue funcionando.
- Colaboracion UML conserva sus eventos.
- Generacion previa funciona con modelos legacy.
- Vista de estilos no depende de especificaciones incompletas.
- Restauracion de versiones antiguas no falla por campos ausentes.

---

## 64. Orden obligatorio de implementacion

1. Auditar contratos de Fase 1 presentes.
2. Completar modelo ORM y relaciones si falta algo.
3. Completar DTO Pydantic estrictos.
4. Implementar normalizadores.
5. Implementar resolucion de referencias.
6. Implementar validacion por niveles.
7. Completar CRUD de parametros.
8. Implementar servicio y API de especificacion.
9. Agregar revision/concurrencia.
10. Integrar auditoria y eventos posteriores al commit.
11. Extender contexto y salida IA.
12. Implementar propuesta y confirmacion.
13. Extender modelo interno.
14. Extender modelo intermedio versionado.
15. Integrar snapshot.
16. Integrar XMI compatible.
17. Implementar editor frontend.
18. Integrar propuesta IA y comparacion.
19. Agregar pruebas backend.
20. Agregar pruebas frontend.
21. Ejecutar regresion de UML y generadores.
22. Documentar decisiones y limitaciones.

No empezar por la interfaz antes de fijar DTO y reglas de validacion.

---

## 65. Comandos de verificacion

Adaptar a los comandos reales del repositorio y documentar salida:

```powershell
cd backend
alembic upgrade head
pytest
```

```powershell
cd frontend
npm install
npm run test -- --run
npm run build
```

Agregar pruebas focalizadas, por ejemplo:

```powershell
cd backend
pytest tests/test_method_specifications.py -q
pytest tests/test_generation_intermediate_model.py -q
pytest tests/test_phase6_uml_engine.py -q
```

No afirmar que un comando paso si no fue ejecutado. Si una suite depende de infraestructura externa, explicar como fue simulada o por que se omitio.

---

## 66. Documentacion a producir durante la implementacion

Crear dentro de una carpeta de Fase 4 de la segunda parte:

```text
00_indice_fase4.md
01_modelo_especificacion_metodos.md
02_contratos_backend_frontend.md
03_validacion_referencias_completitud.md
04_refinamiento_ia.md
05_editor_especificaciones.md
06_modelo_intermedio_xmi_versiones.md
07_pruebas_fase4.md
08_resumen_fase4.md
09_acta_cierre_fase4.md
diagramas/
  flujo_especificacion_metodo.mmd
  refinamiento_ia_confirmacion.mmd
  trazabilidad_metodo_generadores.mmd
```

Documentar solo comportamiento real. Incluir ejemplos de metodo interno, API y accion visible.

---

## 67. Entregables

- Modelo y migracion verificados.
- DTO estrictos.
- CRUD de especificacion.
- CRUD completo de parametros.
- Validador determinista.
- Resolutor de referencias.
- Refinamiento IA con propuesta.
- Confirmacion colaborativa segura.
- Editor frontend completo.
- Eventos y auditoria.
- Modelo intermedio v2.
- Integracion XMI/snapshot.
- Pruebas automatizadas.
- Documentacion de fase.

---

## 68. Prohibiciones

- No guardar toda la especificacion solo en `metadata_json`.
- No crear otra tabla si `UmlMethodSpecification` ya existe.
- No aceptar IDs generados por IA sin resolverlos.
- No ejecutar reglas como codigo.
- No aplicar propuestas automaticamente.
- No sobrescribir cambios concurrentes.
- No tratar advertencia como exito silencioso.
- No bloquear metodos legacy sin razon.
- No duplicar contratos para Spring Boot y Flutter.
- No generar backend funcional sin evaluar Flutter para `user_action`.
- No agregar estilos visuales al contrato funcional.
- No emitir WebSocket antes del commit.
- No exponer datos de otro proyecto.
- No depender de Ollama real en pruebas normales.
- No afirmar soporte XMI que no se haya verificado.

---

## 69. Lista final de comprobacion

- [ ] Firma y semantica estan separadas.
- [ ] Parametros tienen CRUD completo.
- [ ] Especificacion uno a uno funciona.
- [ ] Enums estan centralizados.
- [ ] JSONB se valida con modelos tipados.
- [ ] Reglas generables usan un bloque estructurado sin codigo libre.
- [ ] Referencias usan IDs reales.
- [ ] Ambiguedades se informan.
- [ ] Contrato backend es valido.
- [ ] Contrato Flutter es valido.
- [ ] Ambos contratos son coherentes.
- [ ] Estados de completitud son reproducibles.
- [ ] Borradores pueden guardarse.
- [ ] Solo `ready` cumple validacion estricta.
- [ ] IA devuelve propuesta estructurada.
- [ ] Propuesta requiere confirmacion.
- [ ] Solicitudes multiples permanecen separadas.
- [ ] Concurrencia no pierde cambios.
- [ ] Auditoria registra actor real.
- [ ] WebSocket sincroniza despues del commit.
- [ ] Modelo intermedio contiene parametros y especificacion.
- [ ] V1 sigue siendo compatible.
- [ ] XMI conserva lo soportado.
- [ ] Snapshot contiene especificaciones.
- [ ] Metodos legacy no se rompen.
- [ ] Pruebas backend pasan.
- [ ] Pruebas frontend pasan.
- [ ] Build frontend pasa.
- [ ] No hay secretos ni contenido ejecutable.

---

## 70. Informe final requerido

Al concluir la implementacion, reportar:

1. Archivos modificados.
2. Migracion usada o verificada.
3. Esquema final de especificacion.
4. Endpoints agregados.
5. Reglas de validacion.
6. Estrategia de referencias.
7. Flujo IA y confirmacion.
8. Integracion colaborativa.
9. Version del modelo intermedio.
10. Conservacion XMI y snapshots.
11. Pruebas ejecutadas y resultados exactos.
12. Casos manuales verificados.
13. Limitaciones reales.
14. Contratos que consumira la Fase 5.

---

## 71. Resultado final esperado

CASE Inteligente debe dejar de tratar los metodos UML como simples nombres decorativos. Cada metodo funcional debe poder expresar una operacion de dominio completa, con entradas, salida, condiciones, reglas, validaciones, permisos, efectos y exposicion.

El usuario puede construir esa especificacion manualmente o pedir ayuda a la misma IA colaborativa del proyecto. La IA interpreta lenguaje natural, pero el sistema valida cada referencia contra el diagrama actual y presenta una propuesta revisable antes de persistir.

El resultado queda guardado, sincronizado, auditable, versionable y disponible en un modelo intermedio comun. De esta forma, la Fase 5 podra generar Spring Boot y Flutter desde el mismo contrato, evitando que una operacion exista en backend sin que su representacion movil haya sido evaluada, y evitando que Flutter invente rutas o parametros distintos al backend.
