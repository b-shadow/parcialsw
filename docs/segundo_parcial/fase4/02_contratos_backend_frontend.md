# Contratos backend y Flutter

## Contrato backend

`BackendMethodContract` describe una operacion generable sin incluir codigo arbitrario:

- metodo HTTP: GET, POST, PUT, PATCH o DELETE;
- ruta relativa segura;
- DTO de entrada y salida;
- limite transaccional;
- autorizaciones;
- codigos de error estables;
- estados HTTP de exito, validacion, no encontrado y conflicto.

Las rutas absolutas, segmentos `..`, espacios, fragmentos y consultas fijas se rechazan. Los parametros `{nombre}` deben existir en la firma UML. Una operacion mutante con GET produce un error de validacion.

## Contrato Flutter

`FlutterMethodContract` especifica:

- interaccion: formulario, boton, menu, segundo plano o filtro;
- etiqueta y ubicacion;
- confirmacion previa;
- objetivos a refrescar por UUID;
- mensaje de exito;
- correspondencia entre parametros y controles.

Cada campo enlaza un parametro real. Los controles admitidos son texto, texto multilinea, entero, decimal, interruptor, fecha, fecha y hora, seleccion simple, selector de entidad y seleccion multiple.

Un selector de entidad debe declarar `source_entity_id`. Sus `display_fields` deben existir como atributos de esa clase. De esta manera el generador puede producir una seleccion `Estudiante` o `Curso` usando atributos reales en vez de inferir nombres durante la generacion.

## Correspondencia de tipos

| Tipo UML | Control recomendado |
| --- | --- |
| `String`, `char`, `text` | `text_input` |
| `int`, `Integer`, `long` | `number_input` |
| `double`, `float`, `decimal` | `decimal_input` |
| `boolean`, `bool` | `switch` |
| `Date`, `LocalDate` | `date_picker` |
| `DateTime`, `LocalDateTime`, `timestamp` | `date_time_picker` |
| UUID relacionado | `entity_selector` |

Una diferencia de control compatible se reporta como advertencia; una referencia inexistente se reporta como error bloqueante.

## API REST

| Metodo | Ruta | Funcion |
| --- | --- | --- |
| GET | `/api/v1/uml/methods/{id}/specification` | Leer contrato y readiness |
| PUT | `/api/v1/uml/methods/{id}/specification` | Crear o reemplazar con precondicion |
| PATCH | `/api/v1/uml/methods/{id}/specification` | Actualizar campos con revision |
| DELETE | `/api/v1/uml/methods/{id}/specification` | Eliminar con revision |
| POST | `/api/v1/uml/methods/{id}/specification/validate` | Validar borrador o estricto |
| POST | `/api/v1/uml/methods/{id}/specification/refine` | Crear propuesta asistida |
| PATCH | `/api/v1/uml/parameters/{id}` | Modificar parametro |
| DELETE | `/api/v1/uml/parameters/{id}` | Eliminar parametro no referenciado |

La autorizacion se resuelve mediante autenticacion, pertenencia al proyecto y rol `EDITOR` u `ORGANIZADOR` para escritura. La lectura y validacion requieren membresia.

