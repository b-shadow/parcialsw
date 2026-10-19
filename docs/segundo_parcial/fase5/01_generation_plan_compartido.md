# GenerationPlan compartido

## Decision arquitectonica

`GenerationPlan` es la frontera entre el modelo UML validado y los emisores. Es un conjunto de modelos Pydantic congelados (`frozen=True`, `extra=forbid`) y no puede mutarse durante la generacion.

## Contenido

- Proyecto: nombre Java, artefacto, paquete Dart y paquete base Java.
- Entidades y campos con nombres fuente y normalizados.
- Registro logico de tipos: Java, Dart, JSON y formato.
- Operaciones: propietario, clase de operacion, exposicion y efectos.
- Parametros con ubicacion `path`, `query`, `body` o `context`.
- Rutas contractuales y efectivas bajo `/api`.
- DTO de solicitud y respuesta.
- Reglas estructuradas y codigos de error.
- Acciones Flutter con control, selector, etiqueta y refresco.
- Diagnosticos y huella SHA-256 canonica.

## Compatibilidad

El adaptador existente convierte modelos v1 a v2 sin modificar el diccionario recibido. Los metodos heredados quedan en estado `legacy` y no producen comportamiento funcional inventado. El CRUD historico sigue generandose.

## Determinismo

La huella se calcula sobre JSON ordenado y compacto. Dos entradas equivalentes producen el mismo hash. El mismo plan completo se escribe como `generation-plan.json` en Spring Boot y Flutter.

## Regla de propiedad

Solo `plan_compiler.py` interpreta el modelo intermedio. Los emisores no vuelven a decidir nombres, verbos, ubicaciones de parametros ni controles.
