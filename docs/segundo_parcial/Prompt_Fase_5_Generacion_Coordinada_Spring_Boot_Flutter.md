# PROMPT FASE 5: GENERACION COORDINADA SPRING BOOT Y FLUTTER

## 0. Instruccion maestra

Implementar la Fase 5 de la segunda parte de CASE Inteligente: ampliar los generadores existentes para convertir el modelo intermedio funcional de la Fase 4 en un backend Spring Boot y un frontend Flutter coherentes, ejecutables y verificables.

Ambos proyectos deben derivarse de un unico plan de generacion. No interpretar por separado nombres, rutas, tipos, parametros, validaciones o permisos en cada generador. El backend y Flutter deben compartir exactamente el mismo contrato de operaciones.

La implementacion debe conservar:

- CRUD y relaciones ya generados.
- Reglas de multiplicidad.
- Association classes.
- Formularios de fecha, booleanos, numeros y relaciones.
- Configuracion visual Flutter ya soportada.
- Scripts de arranque y descarga ZIP.
- Compatibilidad con transformaciones anteriores.

Esta fase debe generar codigo solo desde estructuras validadas. Las descripciones humanas pueden aparecer en documentacion, etiquetas o mensajes, pero no deben convertirse directamente en Java, Dart, SQL o expresiones ejecutables.

---

## 1. Resultado funcional buscado

Al terminar:

1. Un metodo `ready` de Fase 4 genera comportamiento backend determinista.
2. Un metodo `api` genera servicio, endpoint y DTO, pero no necesariamente control visual.
3. Un metodo `user_action` genera backend y una accion Flutter funcional.
4. Un metodo `internal` genera servicio interno sin endpoint ni interfaz.
5. Flutter utiliza exactamente el metodo HTTP, ruta y payload generados en Spring Boot.
6. Los parametros UML tienen el mismo nombre y tipo logico en ambos proyectos.
7. Las referencias a entidades producen IDs y selectores consistentes.
8. Fechas, numeros, booleanos, textos y colecciones usan controles correctos.
9. Las reglas soportadas generan validacion y pruebas.
10. Las reglas no soportadas bloquean la generacion semantica con diagnostico claro.
11. Los proyectos legacy continuan generando el CRUD previo.
12. El backend generado compila y sus pruebas pasan.
13. Flutter supera `flutter analyze`, pruebas y compilacion de verificacion cuando el SDK esta disponible.
14. Solo se publican artefactos finales si la validacion coordinada es satisfactoria.

---

## 2. Alineacion obligatoria entre fases

### Fase 1

Consumir:

- Transformaciones y artefactos persistidos.
- Contratos versionados.
- Configuracion de generacion.
- Configuracion visual Flutter.
- Estados y manifiestos de generacion.

### Fase 2

La IA puede ayudar a completar especificaciones antes de generar. No usar Qwen para escribir archivos finales de manera no determinista. La generacion final debe ser reproducible para la misma entrada.

### Fase 3

Publicar estado y resultado de generacion mediante los eventos colaborativos definidos. La solicitud identifica al usuario autenticado y aparece en la actividad compartida.

### Fase 4

Consumir exclusivamente:

- Firma UML.
- Parametros ordenados.
- `operation_kind`.
- `exposure`.
- Condiciones, reglas, validaciones, efectos y permisos.
- `backend_contract`.
- `frontend_contract`.
- Referencias resueltas.
- Estado de preparacion.
- Modelo intermedio `schema_version: 2`.

### Entrega a Fase 6

Exponer un manifiesto de UI generado que permita al preview representar:

- Pantallas.
- Formularios.
- Acciones.
- Controles.
- Etiquetas.
- Estados.
- Tema efectivo.

La Fase 6 personalizara y previsualizara estilos sin redefinir la semantica de las operaciones.

---

## 3. Regla central no negociable

Ningun metodo funcional se interpreta dos veces.

Flujo obligatorio:

```text
UmlTransformation v2
    -> validacion semantica
    -> GenerationPlan comun e inmutable
        -> SpringBootEmitter
        -> FlutterEmitter
    -> CrossContractValidator
    -> verificadores de compilacion
    -> manifiestos y ZIP
```

Para `user_action`, si no se puede construir una representacion Flutter valida, tampoco se publica el backend coordinado de esa operacion. El usuario debe corregir la especificacion.

Solo `internal` omite endpoint e interfaz. `api` omite interfaz directa, pero genera backend. `user_action` exige ambos.

---

## 4. Precondiciones

Verificar antes de implementar:

- La transformacion v2 incluye parametros y especificaciones.
- El estado `ready_for_generation` se calcula en backend.
- Las referencias UML usan IDs reales.
- Los contratos backend y Flutter pasaron validacion estricta.
- Los generadores actuales pasan sus pruebas de multiplicidad y association class.
- El ZIP Spring Boot contiene proyecto Maven, Docker Compose, scripts y PostgreSQL.
- El ZIP Flutter contiene fuentes, web y Android cuando el SDK esta disponible.
- El tema Flutter actual llega a plantillas.
- Los endpoints de generacion verifican membresia.

Una dependencia ausente se completa en su fase propietaria. No reemplazarla con valores inventados.

---

## 5. Alcance exacto

- Preflight coordinado.
- Plan de generacion tipado e inmutable.
- Adaptador de modelo intermedio v1 y lector v2.
- Catalogo de tipos comun.
- Catalogo de operaciones generables.
- Compilacion de contratos de ruta y DTO.
- Servicios y endpoints Spring Boot.
- Repositorios y consultas requeridas.
- Validaciones y reglas soportadas.
- Excepciones y respuestas de error.
- Autorizacion cuando exista permiso declarado.
- Pruebas Java generadas.
- Cliente HTTP Flutter.
- Acciones, formularios, filtros y confirmaciones Flutter.
- Selectores de referencias.
- Estados de carga, exito, vacio y error.
- Refresco posterior a operaciones.
- Pruebas Dart generadas.
- Validacion cruzada backend-frontend.
- Compilacion/verificacion de artefactos.
- Generacion coordinada y endpoints legacy compatibles.
- Manifiestos, checksums y documentacion de ejecucion.
- Pruebas automatizadas del generador.

---

## 6. Fuera de alcance

- Inventar implementaciones para reglas ambiguas.
- Generar codigo libre mediante LLM.
- Implementar un proveedor de identidad completo dentro de cada proyecto.
- Completar el editor visual de Fase 6.
- Cambiar la politica global de versiones de Fase 7.
- Implementar la PWA reducida de Fase 8.
- Desplegar automaticamente los proyectos generados.
- Editar manualmente los repositorios descargados para que compilen.

El producto generado debe funcionar desde el ZIP y comandos documentados, sin correcciones manuales del codigo.

---

## 7. Herramientas y tecnologias

### Orquestador de generacion

- Python.
- Pydantic o dataclasses tipadas para el plan.
- Servicios FastAPI existentes.
- SQLAlchemy para registros de generacion.
- `pathlib` para rutas.
- `tempfile` o directorios staging dentro del almacenamiento configurado.
- `hashlib` para checksums.
- `zipfile` para artefactos.

### Backend generado

- Java 17.
- Spring Boot en la version fijada por el repositorio.
- Maven.
- Spring Web.
- Spring Data JPA.
- Jakarta Validation.
- Spring Security solo cuando corresponda.
- PostgreSQL.
- JUnit 5, Mockito y MockMvc.
- SpringDoc/OpenAPI.

### Frontend generado

- Flutter/Dart en la version documentada por el entorno.
- Paquete `http` existente o cliente adoptado por el generador.
- `ChangeNotifier` y providers actuales, salvo que el repositorio ya migre de forma global.
- Material 3.
- `flutter_test`.

### Verificacion

- `mvnw.cmd`/`mvnw` o Maven instalado.
- `flutter analyze`.
- `flutter test`.
- `flutter build web` como compilacion portable inicial.
- Opcionalmente `flutter build apk --debug` cuando Android SDK este disponible.

No descargar herramientas silenciosamente durante pruebas unitarias. Las pruebas de plantillas deben poder usar dobles o verificadores sintacticos sin red.

---

## 8. Linea base actual

El backend actual genera:

- Entidades JPA.
- Repositorios CRUD.
- DTO de entidad.
- Servicios CRUD.
- Controladores CRUD.
- Excepciones basicas.
- Seguridad permisiva.
- PostgreSQL y scripts.

Flutter genera:

- Modelos.
- Servicios HTTP CRUD.
- Providers.
- Listas.
- Formularios.
- Fechas, booleanos y selectores de relacion.
- Tema y boton compartido.
- Web y Android cuando existe Flutter CLI.

La brecha es generar operaciones de metodos UML y garantizar que ambos lados compartan contrato. No eliminar la base CRUD existente.

---

## 9. Arquitectura interna propuesta

Estructura orientativa:

```text
generacion_software/
  coordinated_generator/
    contracts/
      generation_plan.py
      operation_plan.py
      dto_plan.py
      ui_action_plan.py
      diagnostics.py
    adapters/
      intermediate_v1.py
      intermediate_v2.py
    compiler/
      plan_compiler.py
      type_registry.py
      route_registry.py
      rule_compiler.py
      ui_compiler.py
    validators/
      preflight_validator.py
      cross_contract_validator.py
    services/
      coordinated_generation_service.py
  backend_generator/
    analyzer/
    templates/
    generator/
  flutter_generator/
    uml_analyzer/
    templates/
    generator/
```

Adaptar nombres a convenciones reales. Evitar un archivo monolitico con cientos de condiciones mezcladas.

---

## 10. `GenerationPlan`

El plan debe ser tipado, serializable e inmutable durante emision:

```json
{
  "schema_version": 1,
  "source_transformation_id": "uuid",
  "source_model_version": 2,
  "project": {
    "name": "SistemaAcademico",
    "base_package": "com.caseinteligente.generated.sistemaacademico",
    "api_prefix": "/api"
  },
  "entities": [],
  "relationships": [],
  "operations": [],
  "routes": [],
  "dtos": [],
  "ui_actions": [],
  "theme": {},
  "diagnostics": []
}
```

El plan contiene nombres ya normalizados. Las plantillas no vuelven a inferir semantica ni consultar el UML original.

---

## 11. `OperationPlan`

Campos minimos:

```json
{
  "id": "uuid-del-metodo",
  "owner_entity_id": "uuid-clase",
  "owner_entity": "Inscripcion",
  "source_name": "inscribir",
  "java_name": "inscribir",
  "dart_name": "inscribir",
  "operation_kind": "business_action",
  "exposure": "user_action",
  "return_type": {
    "logical": "entity_reference",
    "source": "Inscripcion",
    "java": "InscripcionResponse",
    "dart": "Inscripcion"
  },
  "parameters": [],
  "backend": {},
  "frontend": {},
  "rules": [],
  "permissions": [],
  "side_effects": []
}
```

Cada operacion conserva el ID UML para trazabilidad en manifiestos y errores.

---

## 12. Preflight coordinado

Antes de escribir archivos:

1. Validar version del modelo intermedio.
2. Adaptar v1 solo al modo legacy.
3. Validar clases, atributos, relaciones y multiplicidades.
4. Validar estado de cada metodo.
5. Clasificar metodo como legacy, internal, api o user_action.
6. Resolver tipos.
7. Construir rutas.
8. Detectar colisiones.
9. Construir DTO.
10. Compilar reglas soportadas.
11. Construir acciones Flutter.
12. Validar coherencia cruzada.
13. Devolver diagnosticos sin escribir artefactos si existe un error.

El preflight debe poder ejecutarse desde API sin generar ZIP.

---

## 13. Politica para estados de Fase 4

- `legacy`: usar comportamiento CRUD anterior.
- `ready`: incluir en generacion semantica.
- `empty`: tratar como legacy solo si nunca se inicio especificacion.
- `draft`: bloquear generacion coordinada del modelo v2.
- `needs_review`: bloquear hasta confirmar/rechazar propuesta.
- `invalid`: bloquear.

No omitir silenciosamente metodos en borrador. El preflight devuelve clase, metodo, campo y diagnostico.

Permitir un modo explicito `legacy_only` para reproducir generacion anterior, sin afirmar que los metodos funcionales fueron implementados.

---

## 14. Registro de tipos comun

Definir una sola tabla logica:

| Tipo logico | UML | Java | Dart | JSON |
| --- | --- | --- | --- | --- |
| texto | String, char, text | String | String | string |
| entero | Integer, int, Long | Integer/Long | int | integer |
| decimal | Double, Float, Decimal | Double/BigDecimal | double | number |
| booleano | Boolean, bool | Boolean | bool | boolean |
| fecha | Date | LocalDate | DateTime | `YYYY-MM-DD` |
| fecha-hora | DateTime | LocalDateTime | DateTime | ISO 8601 |
| uuid | UUID | UUID | String | string uuid |
| entidad | clase UML | DTO/entidad | modelo | object o uuid segun contrato |
| lista | multiplicidad | List<T> | List<T> | array |
| vacio | void | void | Future<void> | sin cuerpo |

El registro produce tambien:

- Imports.
- Conversores JSON.
- Validadores.
- Control Flutter sugerido.
- Comparacion de compatibilidad.

Un tipo desconocido genera error; no degradar siempre a `String` en modo semantico.

---

## 15. Normalizacion de nombres

Centralizar:

- PascalCase para clases y DTO Java/Dart.
- camelCase para campos, parametros y metodos.
- kebab-case o segmentos seguros para rutas.
- snake_case para archivos/modulos Dart.
- UPPER_SNAKE_CASE para codigos de error.

Conservar nombre original en metadatos.

Detectar colisiones posteriores a normalizacion:

- `registrar_pago` y `registrar-pago`.
- Clases con mismo PascalCase.
- Rutas equivalentes con slash final.
- DTO con nombre reservado.
- Palabras reservadas Java o Dart.

No resolver colisiones agregando sufijos invisibles sin diagnostico.

---

## 16. Registro de rutas

La ruta efectiva se compone una sola vez:

```text
api_prefix + backend_contract.path
```

Ejemplo:

```text
/api + /inscripciones = /api/inscripciones
```

El plan almacena:

- Metodo HTTP.
- Ruta contractual.
- Ruta efectiva.
- Parametros path.
- Parametros query.
- Cuerpo.
- Tipo de respuesta.
- Codigos HTTP.
- Permisos.
- Operacion propietaria.

Validar colision por pareja `HTTP + ruta efectiva`, incluyendo rutas CRUD heredadas.

---

## 17. DTO compartidos

Crear `DtoPlan` antes de emitir Java o Dart:

```json
{
  "name": "CrearInscripcionRequest",
  "direction": "request",
  "fields": [
    {
      "source_parameter_id": "uuid",
      "json_name": "estudianteId",
      "logical_type": "uuid",
      "required": true,
      "constraints": []
    }
  ]
}
```

Reglas:

- `json_name` identico en backend y Flutter.
- Campos ordenados de forma estable.
- Nullable identico.
- Fechas con formato identico.
- Entidad de entrada usa ID salvo contrato estructurado explicito.
- Respuesta de entidad usa DTO, no entidad JPA directa.
- Lista usa arreglo JSON.
- `void` no inventa objeto vacio.

Reutilizar DTO iguales solo si estructura y semantica coinciden completamente.

---

## 18. Clasificacion por `operation_kind`

### `create`

- Servicio transaccional.
- Validacion de entrada.
- Construccion de entidad.
- Resolucion de referencias.
- Persistencia.
- Respuesta y codigo 201.

### `read`

- Consulta por identificador o parametros.
- `@Transactional(readOnly = true)`.
- 404 controlado.

### `search`

- Parametros query.
- Repositorio con consulta derivada o especificacion soportada.
- Lista vacia valida.
- Filtros opcionales segun contrato.

### `update`

- Busca entidad.
- Aplica campos permitidos.
- Valida reglas.
- Guarda y responde.

### `delete`

- Confirma existencia.
- Verifica reglas soportadas.
- Elimina o desactiva solo segun especificacion estructurada.
- Responde 204 o contrato declarado.

### `calculate`

- Metodo de servicio determinista.
- No persiste salvo efecto secundario explicito y soportado.

### `business_action`

- Usa plantilla de accion de dominio basada en efectos y referencias estructuradas.
- Bloquea si la descripcion no puede compilarse de forma determinista.

### `custom`

- Solo generable si el contrato contiene una estrategia soportada completa.
- No generar cuerpo con `TODO` como si estuviera terminado.

---

## 19. Catalogo de reglas generables

Definir un catalogo cerrado inicial. Ejemplos:

- `required`.
- `not_blank`.
- `min_length`.
- `max_length`.
- `min_value`.
- `max_value`.
- `range`.
- `email`.
- `pattern` seguro.
- `entity_exists`.
- `unique_by_fields`.
- `state_equals`.
- `state_in`.
- `not_duplicate_relation`.

Cada compilador recibe una estructura validada, no analiza prosa.

Si Fase 4 solo contiene descripcion sin operandos suficientes:

- Marcar `unsupported_rule_for_generation`.
- Indicar campos estructurados faltantes.
- No inventar consulta ni expresion.
- Permitir que el usuario refine la especificacion antes de reintentar.

---

## 20. Representacion estructurada de regla compilable

Extender de forma compatible el objeto de regla de Fase 4 con un bloque opcional `generation`:

```json
{
  "code": "duplicate_enrollment",
  "description": "No puede repetirse estudiante y curso",
  "severity": "error",
  "error_code": "DUPLICATE_ENROLLMENT",
  "generation": {
    "kind": "unique_by_fields",
    "entity_id": "uuid-inscripcion",
    "fields": ["estudianteId", "cursoId"]
  }
}
```

Fase 5 consume este bloque. Si esta ausente, puede generar documentacion y una prueba descriptiva, pero no una implementacion ficticia. Actualizar DTO de Fase 4 de forma aditiva y versionada.

---

## 21. Diagnosticos de preflight

Formato:

```json
{
  "code": "unsupported_rule_for_generation",
  "severity": "error",
  "method_id": "uuid",
  "path": "business_rules[0].generation",
  "message": "La regla duplicate_enrollment no define campos comparables",
  "suggestion": "Seleccione los campos estudianteId y cursoId"
}
```

Codigos minimos:

- `unsupported_model_version`.
- `method_not_ready`.
- `unknown_type`.
- `route_collision`.
- `dto_name_collision`.
- `missing_flutter_action`.
- `unknown_ui_control`.
- `unsupported_rule_for_generation`.
- `unresolved_entity_reference`.
- `permission_without_security_contract`.
- `backend_flutter_mismatch`.

---

## 22. Modelo Spring Boot ampliado

Extender `SpringBootProject` con:

- Operaciones.
- DTO funcionales.
- Reglas compiladas.
- Consultas de repositorio.
- Permisos.
- Rutas.
- Clases de prueba.
- Configuracion de seguridad efectiva.

Agregar dataclasses/tipos como:

- `JavaOperation`.
- `JavaParameter`.
- `JavaDto`.
- `JavaDtoField`.
- `JavaValidation`.
- `JavaRepositoryQuery`.
- `JavaPermission`.
- `JavaTestCase`.

No pasar diccionarios arbitrarios directamente a las plantillas.

---

## 23. Capas Spring Boot generadas

Estructura objetivo:

```text
src/main/java/<package>/
  config/
  controller/
  dto/
  entity/
  exception/
  repository/
  service/
  validation/
src/test/java/<package>/
  controller/
  service/
```

Cada operacion debe ubicarse en la clase propietaria o en un servicio de dominio explicitamente derivado. Evitar una clase global con todos los metodos.

---

## 24. Servicios Spring Boot

Generar:

- Metodo con nombre y tipos del plan.
- `@Transactional` para escrituras.
- `@Transactional(readOnly = true)` para consultas.
- Validacion de precondiciones compilables.
- Carga de entidades relacionadas mediante repositorios.
- Regla de negocio compilable.
- Efectos persistentes soportados.
- Mapeo a respuesta.
- Excepcion de dominio con codigo estable.

No:

- Devolver entidades JPA directamente.
- Usar `RuntimeException` generica para errores esperados.
- Dejar `return null` o `UnsupportedOperationException` en un artefacto marcado exitoso.
- Inyectar repositorios no utilizados.

---

## 25. Repositorios Spring Data

Generar consultas solo desde reglas estructuradas:

```java
boolean existsByEstudianteIdAndCursoId(UUID estudianteId, UUID cursoId);
```

Reglas:

- Nombres derivados validos para propiedades reales.
- `@Query` solo desde una plantilla cerrada, nunca SQL/JPQL libre de usuario.
- Consultas de busqueda combinan filtros soportados.
- Paginacion solo si contrato la declara.
- Association class usa las FK ya generadas.
- Multiplicidad decide propiedad y cardinalidad, no el texto del metodo.

---

## 26. DTO y validacion Jakarta

Mapeo inicial:

- Obligatorio: `@NotNull`.
- Texto obligatorio: `@NotBlank`.
- Longitud: `@Size`.
- Numero minimo/maximo: `@Min`, `@Max`, `@DecimalMin`, `@DecimalMax`.
- Correo: `@Email`.
- Patron seguro: `@Pattern` con literal escapado.
- Coleccion no vacia: `@NotEmpty`.

No generar anotaciones contradictorias. Las reglas de dominio que requieren base de datos pertenecen al servicio, no al DTO.

---

## 27. Controladores Spring Boot

Para `api` y `user_action`:

- Usar ruta efectiva del plan.
- Usar anotacion HTTP correcta.
- Separar path, query y body.
- Aplicar `@Valid`.
- Devolver codigo de estado contractual.
- Delegar al servicio.
- Documentar con OpenAPI de manera consistente.
- Aplicar autorizacion declarada.

Para `internal`:

- No generar metodo de controlador.
- No incluir ruta en manifiesto publico.

No duplicar una ruta CRUD existente. El preflight debe decidir si una operacion reemplaza, complementa o colisiona.

---

## 28. Errores Spring Boot

Generar un sobre estable:

```json
{
  "timestamp": "ISO-8601",
  "status": 409,
  "code": "DUPLICATE_ENROLLMENT",
  "message": "La inscripcion ya existe",
  "fieldErrors": {}
}
```

Clases:

- `ApiError`.
- `DomainException` con codigo y estado.
- `ResourceNotFoundException`.
- `GlobalExceptionHandler`.

Flutter debe decodificar este contrato y mostrar `message` segura. No mostrar stack traces.

---

## 29. Seguridad generada

Si no existen permisos requeridos:

- Conservar configuracion simple documentada para desarrollo.

Si existe al menos un permiso:

- Habilitar method security.
- Generar `@PreAuthorize("hasAuthority('permission.code')")` con valores escapados y validados.
- Configurar autenticacion Bearer JWT mediante una estrategia determinista soportada.
- Usar secreto o clave configurada por entorno, nunca incrustada.
- Agregar dependencias necesarias.
- Producir `.env.example` sin credenciales reales.
- Generar pruebas con usuario simulado autorizado y no autorizado.

El generador no crea usuarios ni un proveedor de identidad completo. El README debe explicar el contrato de token y como ejecutar en desarrollo. No marcar seguridad como implementada si solo se genera una anotacion sin filtro funcional.

---

## 30. Pruebas Java generadas

Por operacion `ready`, generar casos aplicables:

- Camino exitoso.
- Validacion de entrada.
- Entidad relacionada no encontrada.
- Regla de unicidad.
- Rango invalido.
- Sin permiso.
- Codigo HTTP y cuerpo.
- Repositorio invocado correctamente.
- Operacion de lectura no persiste.

Usar Mockito para servicio y MockMvc para controlador. No requerir PostgreSQL para todas las pruebas unitarias. Agregar una prueba de contexto o integracion acotada si el entorno lo permite.

---

## 31. OpenAPI como artefacto verificable

El backend debe exponer `/v3/api-docs` en ejecucion. Ademas, el generador debe producir un inventario contractual estatico dentro del manifiesto:

```json
{
  "method": "POST",
  "path": "/api/inscripciones",
  "request": "CrearInscripcionRequest",
  "response": "InscripcionResponse",
  "source_method_id": "uuid"
}
```

La validacion cruzada compara Flutter con este inventario sin necesitar iniciar Spring Boot.

---

## 32. Modelo Flutter ampliado

Extender `FlutterProject` con:

- Operaciones.
- DTO de solicitud/respuesta.
- Acciones UI.
- Contratos de error.
- Rutas API.
- Dependencias entre modulos.
- Refrescos.
- Requisitos de autenticacion.

Tipos sugeridos:

- `DartOperation`.
- `DartParameter`.
- `DartRequestModel`.
- `DartResponseModel`.
- `FlutterAction`.
- `FlutterFieldControl`.
- `FlutterRefreshTarget`.

Derivarlos del `GenerationPlan`, no otra vez del UML.

---

## 33. Cliente HTTP Flutter

Ampliar el cliente comun para:

- GET con query parameters.
- POST, PUT, PATCH y DELETE.
- Cuerpo JSON tipado.
- Respuesta vacia 204.
- Listas y objetos.
- Timeout configurable.
- Error de red.
- Error JSON del backend.
- Bearer token opcional mediante proveedor inyectable.
- URL base desde `--dart-define` o configuracion existente.

No codificar una URL de produccion. Conservar soporte para emulador Android y localhost documentado.

---

## 34. Servicios Flutter por operacion

Ejemplo conceptual:

```dart
Future<Inscripcion> inscribir(CrearInscripcionRequest request) async {
  final json = await api.post('/api/inscripciones', body: request.toJson());
  return Inscripcion.fromJson(json as Map<String, dynamic>);
}
```

Reglas:

- Ruta tomada literalmente del plan.
- Nombres JSON identicos al DTO Java.
- Tipo de retorno correcto.
- `Future<void>` para 204.
- Query parameters codificados por URI.
- Fechas serializadas con formato contractual.
- No construir JSON manual diferente en cada pantalla.

---

## 35. Acciones Flutter por ubicacion

Ubicaciones soportadas:

- `list_primary_action`: boton principal o FAB de la lista.
- `list_item_action`: accion por fila.
- `detail_primary_action`: accion principal de detalle.
- `detail_overflow_action`: menu de acciones secundarias.
- `filter_bar`: controles de busqueda.
- `form_submit`: operacion de formulario.

Si Fase 4 usa otro valor no soportado, preflight falla. No colocar todos los botones al final de una pantalla sin considerar contexto.

---

## 36. Formularios funcionales

Para `interaction: form`:

- Crear formulario dedicado o reutilizable.
- Un controlador/estado por parametro editable.
- Validacion cliente equivalente a restricciones simples backend.
- Indicador de campos obligatorios.
- Boton estable durante carga.
- Bloqueo de doble envio.
- Errores por campo cuando backend los provee.
- Error general cuando no hay campo.
- Exito visible.
- Cierre o permanencia segun contrato.
- Refresco de objetivos.

El backend sigue siendo autoridad. Flutter no sustituye validacion de dominio.

---

## 37. Mapeo de controles Flutter

### `text_input`

`TextFormField`, teclado textual y longitud.

### `multiline_text`

`TextFormField` multilinea con limite estable.

### `number_input`

Teclado numerico y parseo `int.tryParse`.

### `decimal_input`

Teclado decimal y parseo controlado independiente de coma/punto segun contrato.

### `date_picker`

Campo de solo lectura, `showDatePicker`, formato `YYYY-MM-DD` para API.

### `date_time_picker`

Fecha y hora, ISO 8601 consistente.

### `switch`

`SwitchListTile` o control binario equivalente.

### `entity_selector`

Carga opciones desde endpoint real, conserva ID y muestra campos configurados.

### `single_select`

Dropdown con opciones cerradas.

### `multi_select`

Selector multiple con lista de IDs.

### `hidden_context`

Valor obtenido de la entidad/pantalla actual; no se muestra como campo editable.

---

## 38. Selectores de entidades

Requisitos:

- Consultar endpoint existente en el inventario backend.
- Usar ID como valor.
- Construir etiqueta con `display_fields` existentes.
- Truncar visualmente texto largo sin perder valor.
- Mostrar carga, vacio y error.
- Permitir reintento.
- Evitar overflow en movil.
- No cargar indefinidamente miles de filas; preparar busqueda/paginacion cuando contrato lo indique.
- Conservar opcion seleccionada al reconstruir widget.

Para association class Inscripcion, Estudiante y Curso deben aparecer como selectores si el contrato asi lo especifica.

---

## 39. Consultas y filtros

Para `search` + `interaction: filter`:

- Generar controles por parametro.
- Omitir query parameter vacio.
- Aplicar debounce a texto si la consulta es interactiva.
- Incluir comando buscar cuando corresponda.
- Mostrar limpiar filtros.
- Conservar estado durante carga.
- Renderizar lista vacia diferenciada de error.
- Cancelar o ignorar respuestas obsoletas.

Backend genera consulta solo para filtros soportados y atributos reales.

---

## 40. Confirmaciones

Generar dialogo antes de:

- `delete`.
- Accion con `confirmation_required: true`.
- Efecto destructivo.

El dialogo muestra etiqueta concreta y no usa mensajes genericos ambiguos. Confirmar ejecuta una sola solicitud. Cancelar no llama API.

---

## 41. Estados de UI

Toda accion asincrona contempla:

- Inicial.
- Cargando.
- Exito.
- Error de validacion.
- Error de negocio.
- Sin conexion.
- No autorizado.
- Vacio, cuando aplica.

No dejar botones activos durante envio. No mostrar excepciones Dart crudas al usuario.

---

## 42. Refresco posterior

`refresh_targets` se resuelve a providers/modulos reales:

- Invalidar lista.
- Recargar detalle.
- Actualizar elemento local desde respuesta.
- Volver a pantalla anterior solo si contrato lo requiere.

No recargar toda la aplicacion. Si un target no existe, preflight falla.

---

## 43. Pruebas Flutter generadas

Generar pruebas aplicables:

- Serializacion request.
- Deserializacion response.
- Servicio usa metodo y ruta correctos.
- Formulario valida requerido.
- Fecha produce formato correcto.
- Selector envia ID, no etiqueta.
- Boton bloquea doble envio.
- Confirmacion cancela o ejecuta.
- Exito refresca target.
- Error backend muestra mensaje.
- Sin permiso oculta o deshabilita accion segun contrato.

Usar cliente HTTP falso/injectable. Las pruebas no llaman red real.

---

## 44. Autorizacion en Flutter

Si una accion exige permiso:

- Cliente puede recibir capacidades/claims del usuario autenticado.
- Ocultar o deshabilitar accion segun politica documentada.
- Enviar Bearer token mediante cliente comun.
- Tratar 401 como sesion no valida.
- Tratar 403 como falta de permiso.

La ocultacion visual no reemplaza `@PreAuthorize` en backend.

Si el proyecto no configura proveedor de identidad, el README explica como inyectar token externo para endpoints protegidos.

---

## 45. Tema y Fase 6

Conservar normalizacion actual:

- Colores.
- Tipografia.
- Radio.
- Estilo de botones.
- Densidad.
- Tema claro/oscuro cuando sea agregado.

Las nuevas pantallas deben usar componentes y tema compartidos:

- `PrimaryActionButton`.
- Inputs tematizados.
- Dialogos y cards del tema.
- Navegacion comun.

No incrustar colores en widgets funcionales. Producir un `ui_manifest.json` que Fase 6 pueda previsualizar.

---

## 46. `ui_manifest.json`

Contenido sugerido:

```json
{
  "schema_version": 1,
  "theme": {},
  "modules": [
    {
      "entity_id": "uuid",
      "name": "Inscripcion",
      "screens": ["list", "detail", "form"],
      "actions": [
        {
          "method_id": "uuid",
          "label": "Inscribir estudiante",
          "placement": "list_primary_action",
          "interaction": "form",
          "fields": []
        }
      ]
    }
  ]
}
```

Debe derivarse del mismo plan que Flutter. No mantener un manifiesto manual separado.

---

## 47. Generacion coordinada atomica

Proceso:

1. Crear registro de ejecucion coordinada.
2. Ejecutar preflight.
3. Crear directorio staging unico.
4. Emitir Spring Boot.
5. Emitir Flutter.
6. Ejecutar validacion cruzada.
7. Ejecutar verificaciones configuradas.
8. Crear manifiestos.
9. Calcular checksums.
10. Crear ZIP individuales y opcional ZIP conjunto.
11. Mover/publicar artefactos finales.
12. Confirmar estados en base de datos.
13. Emitir evento y notificacion.

Ante fallo:

- Marcar ejecucion fallida.
- Guardar diagnostico sanitizado.
- No publicar artefactos parciales como exitosos.
- Limpiar staging de forma segura.
- Mantener ejecuciones anteriores intactas.

---

## 48. Persistencia de ejecucion coordinada

Reutilizar modelos de Fase 1 si ya incluyen agrupacion. Si no existe un agregado, agregar una entidad minima `CoordinatedGeneration`:

```text
id
project_id
transformation_id
requested_by_user_id
backend_id nullable
frontend_id nullable
status
mode
diagnostics_json
manifest_json
created_at
completed_at nullable
```

Estados:

- `queued`.
- `validating`.
- `generating_backend`.
- `generating_frontend`.
- `verifying`.
- `completed`.
- `failed`.
- `cancelled` si existe cancelacion real.

No declarar asincronia distribuida si el proceso sigue en la peticion HTTP. Documentar el comportamiento real.

---

## 49. API de generacion

Mantener endpoints existentes:

```text
POST /api/v1/generation/transform
POST /api/v1/generation/spring-boot
POST /api/v1/generation/flutter
```

Agregar:

```text
POST /api/v1/generation/preflight
POST /api/v1/generation/coordinated
GET  /api/v1/generation/coordinated/{generation_id}
GET  /api/v1/generation/coordinated/{generation_id}/manifest
GET  /api/v1/generation/coordinated/{generation_id}/backend/download
GET  /api/v1/generation/coordinated/{generation_id}/frontend/download
GET  /api/v1/generation/coordinated/{generation_id}/bundle/download
```

Los endpoints individuales usan internamente el mismo plan. Si se solicita Flutter de un `user_action`, verificar que su inventario backend exista en la transformacion o backend asociado.

---

## 50. Solicitud coordinada

```json
{
  "transformation_id": "uuid",
  "backend_name": "SistemaAcademicoApi",
  "frontend_name": "SistemaAcademicoMobile",
  "version_label": "1.0.0",
  "api_base_url": "http://10.0.2.2:8080",
  "mode": "semantic",
  "theme_config": {}
}
```

Reglas:

- `mode`: `semantic` o `legacy_only`.
- `semantic` exige contratos listos.
- URL se valida y solo configura cliente; no se concatena en plantillas sin escape.
- Usuario se obtiene del token.
- La transformacion pertenece al proyecto accesible.
- Idempotencia evita doble generacion accidental con misma clave.

---

## 51. Respuesta de preflight

```json
{
  "can_generate": true,
  "mode": "semantic",
  "source_model_version": 2,
  "summary": {
    "entities": 3,
    "legacy_methods": 0,
    "internal_operations": 1,
    "api_operations": 1,
    "user_actions": 2,
    "routes": 12,
    "ui_actions": 2
  },
  "diagnostics": []
}
```

El frontend debe ejecutar preflight y mostrar errores antes de iniciar trabajo pesado.

---

## 52. Validacion cruzada

Comparar para cada `user_action`:

- Existe ruta backend.
- Metodo HTTP coincide.
- Path coincide.
- Parametros path coinciden.
- Query coincide.
- JSON request coincide.
- Nullable coincide.
- Formato fecha coincide.
- Respuesta coincide.
- Codigos de error estan contemplados.
- Permiso coincide.
- Refrescos apuntan a modulos existentes.

Tambien validar que ninguna llamada Flutter apunte a una ruta ausente. Cualquier diferencia bloquea publicacion.

---

## 53. Manifiesto coordinado

Guardar:

- Version del plan.
- Hash canonico de entrada.
- Transformacion fuente.
- Usuario solicitante.
- Versiones de generadores.
- Backend generado.
- Flutter generado.
- Inventario de rutas.
- Inventario de acciones UI.
- Conteos.
- Comandos de verificacion ejecutados.
- Resultado de cada verificacion.
- Checksums.
- Tema efectivo.
- Diagnosticos no bloqueantes.

No incluir tokens, contrasenas, prompts ni secretos.

---

## 54. Reproducibilidad

La misma entrada, versiones y configuracion deben producir contenido equivalente, salvo:

- IDs de ejecucion.
- Timestamps documentados.
- Orden de ZIP si la libreria no lo fija.

Para mejorar reproducibilidad:

- Ordenar entidades, campos, operaciones y archivos.
- Serializar JSON con claves ordenadas.
- Centralizar versiones de dependencias.
- Evitar valores aleatorios en fuentes.
- Registrar version del generador.
- Calcular hash del plan canonico.

---

## 55. Escritura segura de archivos

- Resolver ruta final dentro del storage root.
- Sanitizar nombres de proyecto.
- Rechazar `..`, separadores y nombres reservados.
- No seguir symlinks fuera del staging.
- Escribir UTF-8.
- Usar finales de linea consistentes.
- No sobrescribir otra ejecucion.
- Crear ZIP con rutas relativas.
- Excluir `.env`, caches, builds y herramientas descargadas.
- Incluir solo `.env.example`.

---

## 56. Scripts de arranque Spring Boot

Conservar `scripts/run.ps1` y `scripts/run.sh`, pero verificar:

- PostgreSQL se inicia por Docker cuando esta disponible.
- Puerto configurable.
- URL y credenciales por entorno.
- Maven Wrapper preferido si se incluye.
- Fallos devuelven codigo distinto de cero.
- No descargan binarios si el usuario esta offline y ya existe herramienta local.
- README ofrece ruta manual equivalente.

El proyecto no debe requerir editar archivos fuente para arrancar.

---

## 57. Scripts de arranque Flutter

Generar scripts o comandos documentados para:

- `flutter pub get`.
- `flutter run` con URL backend.
- Android fisico usando IP LAN.
- Emulador Android usando `10.0.2.2`.
- Web usando URL configurada.
- `flutter analyze`.
- `flutter test`.

No fijar una IP personal en el codigo. Usar `--dart-define=API_BASE_URL=...` o mecanismo equivalente.

---

## 58. CORS y conectividad

El backend generado debe permitir origenes configurables por entorno:

```text
APP_CORS_ALLOWED_ORIGINS=http://localhost:*,https://dominio.example
```

Reglas:

- No usar `*` con credenciales en produccion.
- Flutter movil no depende de CORS, Flutter web si.
- README explica HTTP local y restricciones Android cleartext de desarrollo.
- Produccion recomienda HTTPS.
- No agregar dominios personales fijos al template.

---

## 59. Verificacion Spring Boot

Niveles:

1. Verificacion de estructura y archivos.
2. Analisis del inventario de imports/tipos.
3. `mvn test`.
4. `mvn package` con pruebas.
5. Opcional smoke con PostgreSQL.

Si Maven no esta disponible en el servidor generador:

- No marcar compilacion como aprobada.
- Marcar `verification_status: not_run`.
- Permitir descarga solo si politica del producto lo admite y mostrar advertencia clara.

Para criterio de cierre de la fase, ejecutar compilacion real en el entorno de desarrollo/CI.

---

## 60. Verificacion Flutter

Niveles:

1. Verificacion de estructura.
2. `dart format --set-exit-if-changed` o formateo controlado.
3. `flutter pub get`.
4. `flutter analyze`.
5. `flutter test`.
6. `flutter build web`.
7. Opcional `flutter build apk --debug`.

Si Flutter CLI no existe, distinguir proyecto fuente generado de proyecto compilado. Para cerrar la fase se necesita al menos una ejecucion real en CI o maquina con SDK.

---

## 61. Politica de publicacion de artefactos

Estados posibles por artefacto:

- `generated_unverified`.
- `verified`.
- `failed`.

La UI no debe mostrar `Listo` si solo se escribieron archivos y nunca se compilaron. Mostrar el nivel real.

En modo coordinado estricto:

- Solo `verified` produce estado global `completed`.

En entorno sin toolchain, permitir `generated_unverified` solo con configuracion explicita y diagnostico visible. Nunca confundirlo con criterio de cierre aprobado.

---

## 62. Integracion frontend CASE

En la pantalla Transformacion y generacion:

- Mantener seleccion de proyecto y diagrama.
- Ejecutar transformacion.
- Mostrar preflight.
- Mostrar errores por clase/metodo.
- Permitir abrir el metodo para corregirlo.
- Configurar nombres, URL y tema.
- Iniciar generacion coordinada.
- Mostrar progreso real por etapa.
- Mostrar verificacion backend y Flutter por separado.
- Descargar cada ZIP o bundle.
- Mantener endpoints individuales como opcion avanzada/compatibilidad.

No representar una tarea sincronica como progreso porcentual ficticio. Usar etapas reales.

---

## 63. Eventos colaborativos y notificaciones

Eventos sugeridos:

- `GENERATION_PREFLIGHT_FAILED`.
- `COORDINATED_GENERATION_STARTED`.
- `BACKEND_GENERATION_COMPLETED`.
- `FRONTEND_GENERATION_COMPLETED`.
- `GENERATION_VERIFICATION_COMPLETED`.
- `COORDINATED_GENERATION_COMPLETED`.
- `COORDINATED_GENERATION_FAILED`.

Emitir despues de persistir estado. Notificar a solicitante y colaboradores relevantes al completar/fallar, evitando duplicar push por cada etapa.

---

## 64. Permisos

- Miembro lector puede consultar manifiestos permitidos y descargar si la politica existente lo permite.
- Editor puede transformar/generar segun roles actuales.
- Organizador/creador conserva capacidades administrativas existentes.
- Usuario ajeno no consulta estado ni descarga artefactos.

Aplicar permisos en preflight, ejecucion, estado y descarga. No confiar en IDs del frontend.

---

## 65. Idempotencia y concurrencia

- Solicitud acepta `Idempotency-Key` o `client_request_id`.
- Misma clave, usuario y transformacion retorna misma ejecucion.
- Dos generaciones diferentes usan staging separado.
- No comparten archivos mutables.
- Descargar durante generacion devuelve estado adecuado, no ZIP parcial.
- Reintento tras fallo crea nueva ejecucion o usa una operacion explicita de retry.
- Una transformacion es inmutable; editar UML exige nueva transformacion.

---

## 66. Manejo de errores

Separar:

- Error de preflight: entrada corregible.
- Error de plantilla: defecto del generador.
- Error de toolchain: Maven/Flutter/SDK.
- Error de dependencia: descarga o repositorio.
- Error de filesystem.
- Error de compilacion generada.
- Error de permisos.

Respuesta segura:

```json
{
  "code": "flutter_analysis_failed",
  "stage": "verifying_frontend",
  "message": "Flutter reporto errores de analisis",
  "diagnostics": [],
  "correlation_id": "uuid"
}
```

Guardar salida truncada/sanitizada para diagnostico administrativo. No devolver rutas internas completas ni secretos.

---

## 67. Timeouts y recursos

- Timeout por scaffolding Flutter.
- Timeout por Maven.
- Timeout por Flutter analyze/test/build.
- Limite de tamano del modelo.
- Limite de archivos y ZIP.
- Limite de ejecuciones concurrentes.
- Limpieza de staging antiguo.
- Cancelacion del subproceso al vencer timeout.

No bloquear indefinidamente un worker HTTP. Si la generacion es larga, usar el mecanismo de tareas real definido por Fase 1; no simular cola en memoria como soporte distribuido.

---

## 68. Seguridad del generador

- Plantillas cerradas.
- Sin `eval` ni ejecucion de texto del usuario.
- Escape de cadenas Java, Dart, YAML, XML, JSON y propiedades.
- Nombres sanitizados.
- Paths confinados.
- Subprocesos con lista de argumentos, sin `shell=True` con entrada del usuario.
- Dependencias con versiones fijadas.
- Sin credenciales en ZIP.
- Sin `.env` real.
- Sin claves AWS.
- Sin logs sensibles.
- Escaneo de artefactos por patrones de secretos antes de publicar.

---

## 69. Observabilidad

Registrar:

- `generation_id`.
- `transformation_id`.
- `project_id`.
- `user_id`.
- `correlation_id`.
- Etapa.
- Duracion.
- Cantidad de entidades/operaciones/rutas.
- Hash del plan.
- Versiones de generadores.
- Resultado de verificacion.
- Codigo de error.

Metricas:

- Generaciones iniciadas/completadas/fallidas.
- Fallos por etapa.
- Duracion por emisor.
- Preflight con errores.
- Compilaciones backend/frontend exitosas.
- Artefactos verificados/no verificados.

---

## 70. Pruebas unitarias del plan

Cubrir:

- Adaptacion v1 legacy.
- Lectura v2.
- Metodo internal.
- Metodo api.
- Metodo user_action.
- Metodo draft bloqueado.
- Tipo desconocido.
- Nombre reservado.
- Colision de ruta.
- DTO request/response.
- Fecha consistente.
- UUID referencia entidad.
- Regla soportada.
- Regla no soportada.
- Permiso valido.
- Control Flutter desconocido.
- Refresh target inexistente.
- Orden determinista.
- Hash canonico estable.

---

## 71. Pruebas del generador Spring Boot

Conservar pruebas actuales y agregar:

- Servicio por cada operation kind soportado.
- Endpoint solo para api/user_action.
- Metodo internal sin controller.
- DTO con validaciones.
- Repositorio de unicidad.
- Excepcion con codigo.
- Autorizacion generada.
- Association class con accion funcional.
- Multiplicidad y IDs.
- Pruebas Java generadas.
- Manifiesto de rutas.
- Sin `TODO`, `return null` ni placeholder funcional.
- Compilacion Maven real de fixtures representativos.

---

## 72. Pruebas del generador Flutter

Conservar pruebas actuales y agregar:

- Servicio usa ruta exacta.
- Request usa nombres JSON exactos.
- Formulario por user_action.
- Sin UI para internal/api.
- Selector de entidad.
- Fecha y fecha-hora.
- Numero y decimal.
- Switch.
- Filtro search.
- Confirmacion delete.
- Doble envio bloqueado.
- Refresco correcto.
- Errores backend.
- Token opcional.
- UI manifest.
- Textos largos sin overflow evidente.
- `flutter analyze`, `flutter test` y build web reales.

---

## 73. Pruebas cruzadas

Para cada fixture:

1. Crear modelo intermedio.
2. Compilar `GenerationPlan`.
3. Generar ambos proyectos.
4. Extraer inventario backend.
5. Extraer inventario Flutter.
6. Comparar rutas y metodos.
7. Comparar JSON request.
8. Comparar response.
9. Comparar permisos.
10. Verificar controles.

Fixtures minimos:

- CRUD legacy.
- Inscripcion con Estudiante y Curso.
- Busqueda con filtros.
- Calculo interno.
- Eliminacion confirmada.
- Association class.
- Uno a uno.
- Uno a muchos.
- Muchos a muchos implicito.
- Permisos.

---

## 74. Prueba integral de Inscripcion

Modelo:

- Estudiante: id, nombre.
- Curso: id, nombre.
- Inscripcion: id, fecha, estado, notaFinal.
- Association class entre Estudiante y Curso.
- Metodo `inscribir(estudianteId, cursoId, fecha): Inscripcion`.

Reglas:

- Estudiante existe.
- Curso existe.
- No existe duplicado estudiante-curso.
- Fecha obligatoria.

Backend esperado:

- Request DTO.
- Endpoint POST.
- Servicio transaccional.
- Dos consultas de existencia/carga.
- Consulta de duplicado.
- Persistencia de Inscripcion.
- 201.
- 404 y 409 controlados.
- Pruebas.

Flutter esperado:

- Accion `Inscribir estudiante`.
- Formulario.
- Selector Estudiante.
- Selector Curso.
- Date picker.
- Carga y errores.
- POST con IDs y `YYYY-MM-DD`.
- Exito y refresco.
- Sin overflow con etiquetas largas.

Ambos deben compilar sin editar archivos.

---

## 75. Pruebas de regresion

- Generar fixture actual de ventas.
- Generar fixture de multiplicidad.
- Generar association class.
- Verificar scripts de arranque.
- Verificar tema Flutter.
- Verificar fecha local.
- Verificar dropdown de relacion.
- Verificar ZIP y checksums.
- Verificar endpoints de descarga.
- Verificar CORS de plataforma CASE no se altera.
- Verificar generacion individual sigue disponible.

---

## 76. Criterios de aceptacion funcional

### Metodo internal

Genera servicio y prueba, no endpoint ni boton.

### Metodo api

Genera endpoint y servicio. Flutter no agrega boton, pero el inventario reconoce la API.

### Metodo user_action

Genera endpoint, servicio, cliente y control visible.

### Regla incompleta

Preflight falla antes de escribir archivos.

### Contrato inconsistente

Una ruta Flutter distinta a backend produce error cruzado y no publica ZIP.

### Toolchain ausente

El sistema informa `generated_unverified`, no `verified`.

### Toolchain presente

Backend y Flutter pasan verificaciones configuradas.

### Repeticion idempotente

La misma clave no crea duplicados.

---

## 77. Criterios de aceptacion tecnicos

- Un solo `GenerationPlan` alimenta ambos emisores.
- Plantillas no reinterpretan UML.
- No existe codigo generado desde prosa libre.
- No hay rutas Flutter ausentes en backend.
- No hay tipos JSON divergentes.
- No hay artefactos parciales marcados completos.
- Staging se limpia.
- Checksums son correctos.
- Manifiesto no contiene secretos.
- Maven compila fixtures semanticos.
- Flutter analiza y compila fixtures semanticos.
- Pruebas actuales siguen pasando.
- `git diff --check` queda limpio.

---

## 78. Compatibilidad

- Modelo v1 usa adaptador legacy.
- Modelo v2 sin especificaciones puede usar `legacy_only`.
- Endpoints existentes permanecen.
- Respuestas existentes no pierden campos.
- Manifiestos agregan campos de forma aditiva.
- Generacion CRUD sigue disponible.
- Tema Flutter sigue aplicado.
- Multiplicidad y association class mantienen comportamiento.
- Scripts documentados siguen siendo validos.

No migrar artefactos ZIP antiguos; son inmutables.

---

## 79. Orden obligatorio de implementacion

1. Congelar fixtures actuales y ejecutar regresion.
2. Definir contratos del `GenerationPlan`.
3. Implementar adaptadores v1/v2.
4. Implementar registro de tipos y nombres.
5. Implementar registro de rutas y DTO.
6. Implementar catalogo de reglas.
7. Implementar preflight.
8. Extender analizador Spring Boot desde el plan.
9. Extender plantillas de servicio/repositorio/DTO/controller.
10. Generar errores y seguridad.
11. Generar pruebas Java.
12. Extender analizador Flutter desde el plan.
13. Extender cliente HTTP y modelos request/response.
14. Generar acciones, formularios, filtros y confirmaciones.
15. Generar pruebas Flutter.
16. Implementar validador cruzado.
17. Implementar staging y publicacion atomica.
18. Implementar persistencia/API coordinada.
19. Integrar UI CASE.
20. Integrar eventos y notificaciones.
21. Ejecutar compilaciones reales.
22. Corregir regresiones.
23. Documentar.

No comenzar duplicando plantillas antes de definir el plan comun.

---

## 80. Comandos de verificacion del repositorio

```powershell
cd backend
pytest tests/test_phase8_spring_boot_generator.py -q
pytest tests/test_phase9_flutter_generator.py -q
pytest tests/test_coordinated_generation.py -q
pytest
```

```powershell
cd frontend
npm run test -- --run
npm run build
```

Adaptar nombres de archivos nuevos a la implementacion real.

---

## 81. Comandos de verificacion de un backend generado

Windows:

```powershell
docker compose up -d postgres
.\mvnw.cmd test
.\mvnw.cmd package
.\mvnw.cmd spring-boot:run
```

Linux/macOS:

```bash
docker compose up -d postgres
./mvnw test
./mvnw package
./mvnw spring-boot:run
```

Si no se incluye Maven Wrapper, usar `mvn` y documentarlo sin mezclar ambas alternativas.

---

## 82. Comandos de verificacion de Flutter generado

```powershell
flutter pub get
dart format --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build web
```

Android opcional:

```powershell
flutter build apk --debug
flutter run --dart-define=API_BASE_URL=http://IP_LOCAL:8080
```

La guia generada debe indicar que `IP_LOCAL` se reemplaza por la IP accesible desde el dispositivo, sin modificar fuentes.

---

## 83. Documentacion a producir

Crear durante la implementacion:

```text
docs/segundo_parcial/fase5/
  00_indice_fase5.md
  01_generation_plan_compartido.md
  02_preflight_y_diagnosticos.md
  03_generacion_spring_boot_funcional.md
  04_generacion_flutter_funcional.md
  05_validacion_cruzada.md
  06_verificacion_compilacion.md
  07_seguridad_artefactos.md
  08_pruebas_fase5.md
  09_guia_proyectos_generados.md
  10_resumen_fase5.md
  11_acta_cierre_fase5.md
  diagramas/
    flujo_generacion_coordinada.mmd
    trazabilidad_contrato_codigo.mmd
    validacion_cruzada.mmd
```

Documentar resultados reales de Maven y Flutter, no solo comandos esperados.

---

## 84. Entregables

- `GenerationPlan` tipado.
- Adaptadores v1/v2.
- Preflight y diagnosticos.
- Compilador de reglas soportadas.
- Generador Spring Boot semantico.
- Generador Flutter semantico.
- Inventarios de rutas y UI.
- Validador cruzado.
- Ejecucion coordinada.
- API y UI CASE.
- Manifiestos y ZIP.
- Pruebas generadas.
- Pruebas del generador.
- Compilacion real documentada.
- Documentacion completa.

---

## 85. Prohibiciones

- No generar Java/Dart libre con Qwen.
- No interpretar contratos por separado.
- No omitir metodos invalidos silenciosamente.
- No generar `TODO` funcional en artefactos exitosos.
- No usar `return null` como implementacion.
- No marcar verificado sin ejecutar toolchain.
- No publicar ZIP parcial como exitoso.
- No inventar rutas, entidades o permisos.
- No usar SQL/JPQL libre del usuario.
- No incrustar URL, token o secreto personal.
- No usar `shell=True` con entrada del usuario.
- No romper CRUD legacy.
- No romper multiplicidades.
- No romper association classes.
- No duplicar logica de tipos.
- No colocar controles Flutter para `internal`.
- No omitir Flutter para `user_action`.
- No confundir tema con contrato funcional.

---

## 86. Lista final de comprobacion

- [ ] Modelo v1 sigue funcionando.
- [ ] Modelo v2 se valida estrictamente.
- [ ] Plan comun es la unica fuente de emision.
- [ ] Tipos Java/Dart/JSON coinciden.
- [ ] Rutas coinciden.
- [ ] DTO coinciden.
- [ ] Internal no expone endpoint/UI.
- [ ] API expone backend sin UI obligatoria.
- [ ] User action tiene backend y Flutter.
- [ ] Reglas soportadas generan codigo.
- [ ] Reglas incompletas bloquean.
- [ ] Multiplicidades se conservan.
- [ ] Association class se conserva.
- [ ] Selectores envian IDs.
- [ ] Date usa formato estable.
- [ ] Errores tienen contrato comun.
- [ ] Permisos se aplican en backend.
- [ ] Flutter contempla 401/403.
- [ ] Estados de carga/error/exito existen.
- [ ] Doble envio se bloquea.
- [ ] Refresh targets funcionan.
- [ ] Pruebas Java se generan.
- [ ] Pruebas Flutter se generan.
- [ ] Validacion cruzada pasa.
- [ ] Maven test/package pasan.
- [ ] Flutter analyze/test/build pasan.
- [ ] ZIP se produce desde staging.
- [ ] Checksums coinciden.
- [ ] Manifiesto no contiene secretos.
- [ ] Scripts funcionan sin editar codigo.
- [ ] UI CASE muestra estado real.
- [ ] Eventos se emiten despues de persistir.
- [ ] Documentacion refleja resultados reales.

---

## 87. Informe final requerido

Al concluir, reportar:

1. Arquitectura del plan comun.
2. Versiones de modelos soportadas.
3. Tipos y operaciones soportadas.
4. Reglas compilables y limitaciones.
5. Archivos Spring Boot generados.
6. Archivos Flutter generados.
7. Estrategia de seguridad.
8. Validacion cruzada.
9. Staging y publicacion.
10. API/UI coordinada.
11. Pruebas ejecutadas.
12. Resultados exactos de Maven.
13. Resultados exactos de Flutter.
14. Fixtures integrales verificados.
15. Regresiones verificadas.
16. Contratos entregados a Fase 6.

---

## 88. Resultado final esperado

CASE Inteligente debe producir dos proyectos que se comporten como partes de una misma aplicacion, no como artefactos generados de forma independiente. Cada accion visible en Flutter debe llamar a un endpoint real de Spring Boot con el mismo metodo HTTP, ruta, parametros, tipos, reglas y permisos.

Las operaciones internas permanecen en backend. Las APIs sin representacion directa no agregan controles innecesarios. Las acciones de usuario generan formularios, selectores, filtros o botones acordes con su contrato, incluyendo estados de carga, confirmacion, exito, error y refresco.

El sistema debe rechazar especificaciones que no pueda convertir de manera segura, en lugar de producir codigo incompleto que aparente funcionar. Los ZIP publicados deben indicar con honestidad si fueron compilados y verificados. Los proyectos representativos deben iniciar usando solamente los comandos documentados, sin editar los repositorios generados.
