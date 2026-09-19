# Fase 6 - Editor UML colaborativo

## Frontend

El editor en `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx` fue extendido para:

- Cargar el modelo completo del diagrama.
- Mostrar clases con atributos y metodos.
- Persistir movimiento de nodos.
- Editar nombre de clase seleccionada.
- Eliminar clase seleccionada.
- Crear relaciones.
- Ejecutar validacion.
- Exportar XMI.
- Importar XMI desde contenido.
- Generar UML desde texto, voz o imagen como fuentes preparadas.

## Backend

Se agregaron endpoints para:

- Snapshot completo del modelo.
- Edicion y eliminacion de clases.
- Parametros de metodos.
- Edicion y eliminacion de relaciones.
- Persistencia de posicion visual.
- Importacion/exportacion XMI.
- Generacion UML desde fuente textual, voz o imagen.

## Colaboracion

El editor envia eventos WebSocket para:

- `CREATE_CLASS`
- `UPDATE_CLASS`
- `DELETE_CLASS`
- `CREATE_RELATIONSHIP`
- `MOVE_ELEMENT`

El backend valida eventos soportados y responde con acuse o rechazo.
