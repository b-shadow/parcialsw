# Modelo de especificacion de metodos

## Frontera del agregado

El metodo UML sigue siendo la raiz conceptual. Su firma reside en `uml_methods` y `uml_parameters`; la semantica ampliada reside en una unica fila `uml_method_specifications`, enlazada uno a uno mediante `method_id`. La eliminacion del metodo conserva el comportamiento de cascada de la base.

La separacion evita almacenar reglas de negocio dentro de `metadata_json` y permite validar, versionar y consultar el contrato de manera independiente.

## Firma

La firma contiene:

- nombre del metodo;
- visibilidad UML;
- tipo de retorno;
- parametros con identificador estable;
- nombre, tipo, valor por defecto y orden de cada parametro.

Los parametros cuentan con creacion, modificacion y eliminacion REST. No se permite duplicar nombres dentro del mismo metodo. La eliminacion se bloquea cuando la especificacion referencia el parametro.

## Especificacion funcional

`UmlMethodSpecificationBase` define:

- `description`;
- `operation_kind`;
- `exposure`;
- precondiciones, postcondiciones, reglas y validaciones;
- efectos laterales;
- permisos requeridos;
- entidades relacionadas;
- contrato backend;
- contrato Flutter;
- `schema_version`.

Todos los modelos usan `extra=forbid`. Un campo desconocido se rechaza en el limite de entrada, evitando que datos con errores tipograficos queden almacenados pero sean ignorados por los generadores.

## Reglas tipadas

Cada regla tiene codigo `snake_case`, descripcion, severidad, objetivo opcional, codigo de error y una regla de generacion cerrada. El catalogo incluye requerido, rango, longitud, patron, existencia por ID, unicidad, transicion de estado y calculo.

Los objetivos pueden referir parametros, atributos, clases o relaciones por UUID estable. El nombre se conserva para lectura humana, pero no reemplaza al UUID cuando existe ambiguedad.

## Efectos y permisos

Los efectos laterales distinguen cambios de datos, cambios de estado, notificaciones, auditoria y necesidad de refresco. Los permisos usan el formato `recurso.accion`; se normalizan a minusculas y se rechazan valores libres.

## Concurrencia

La columna `revision` comienza en uno y aumenta en cada escritura. Una actualizacion requiere la revision observada por el cliente. Una creacion usa `If-None-Match: *`. Una revision obsoleta responde `409` con:

```json
{"code": "stale_revision", "current_revision": 7}
```

Esto evita que un colaborador sobrescriba silenciosamente el trabajo de otro.

## Persistencia atomica

Las escrituras manuales guardan especificacion y auditoria en una transaccion. La confirmacion de una propuesta de IA usa la misma transaccion para especificacion, revision, auditoria y estado de `ai_action`. Ante una excepcion se ejecuta rollback y la accion se registra como fallida.

