# Editor de especificaciones

## Acceso

Cada metodo del inspector UML incorpora la accion `Especificar`. Esta abre un panel modal vinculado al metodo seleccionado y al diagrama activo. No se crea un editor independiente ni un diagrama nuevo.

## Vista Firma

Permite modificar nombre, visibilidad y retorno. Los parametros se crean, editan, ordenan y eliminan. El identificador del parametro permanece estable y es el utilizado por reglas y campos Flutter.

## Vista Comportamiento

Incluye descripcion, tipo de operacion, exposicion, precondiciones, postcondiciones, reglas de negocio, validaciones, efectos laterales, permisos y entidades relacionadas. Las clases se eligen del diagrama actual para evitar texto libre ambiguo.

## Vista Backend

Configura metodo HTTP, ruta, DTO, transaccion, autorizaciones, errores y estados HTTP. El usuario puede retirar el contrato cuando el metodo pasa a ser interno.

## Vista Flutter

Configura interaccion, etiqueta, ubicacion, mensaje, confirmacion y objetivos de refresco. Para cada parametro se selecciona control, entidad fuente, atributos visibles y visibilidad del campo. Las fechas usan selectores de fecha y los UUID relacionados pueden usar selectores de entidad.

## Vista Validacion

Ejecuta validacion estricta y presenta mensajes por campo. Si hay cambios locales, primero intenta guardarlos; una escritura fallida detiene la validacion para no mostrar resultados sobre una revision antigua.

## Colaboracion

El editor mantiene una sola conexion de proyecto durante su ciclo de vida. Si llega un evento del mismo metodo:

- sin cambios locales: recarga la ultima revision;
- con cambios locales: conserva el borrador y muestra conflicto;
- el usuario decide recargar o continuar revisando.

## Refinamiento

La zona de IA envia una instruccion sobre el metodo actual. La respuesta muestra campos afectados y referencias no resueltas. `Confirmar y aplicar` ejecuta la accion explicita; cerrar o rechazar visualmente no modifica el metodo.

## Ergonomia

El panel usa altura limitada, desplazamiento interno, tabs estables y rejillas adaptables. Los botones de herramientas usan iconos, los controles largos se reorganizan en pantallas estrechas y ninguna etiqueta depende del ancho del viewport para definir su fuente.

