# Fase 6 - Operaciones de modelado

## Operaciones implementadas

### Diagramas

- Crear diagrama.
- Listar diagramas por proyecto.
- Obtener modelo completo del diagrama.
- Validar diagrama.
- Generar diagrama desde fuente.
- Exportar XMI.
- Importar XMI.

### Clases

- Crear clase.
- Listar clases.
- Editar clase.
- Eliminar clase.
- Persistir posicion visual.

### Atributos

- Crear atributo con nombre, tipo, visibilidad, valor inicial, multiplicidad, requerido y restricciones.

### Metodos

- Crear metodo con nombre, visibilidad y tipo de retorno.
- Crear parametros de metodo.

### Relaciones

- Crear relacion.
- Editar relacion.
- Eliminar relacion.
- Validar pertenencia de clases al diagrama.

## Control de consistencia

- Se valida pertenencia del usuario al proyecto antes de operar.
- Se valida existencia de diagrama, clase, metodo y relacion.
- Al eliminar una clase se eliminan primero relaciones asociadas para conservar integridad.
- Los eventos WebSocket desconocidos se rechazan.
