# Fase 5 - Modulos funcionales frontend

## Gestion de acceso, usuarios y seguimiento

Implementado en `frontend/src/modules/gestion_acceso_usuarios/`.

- Pantalla de inicio de sesion.
- Pantalla de registro.
- Perfil de usuario autenticado.
- Dashboard de reportes.
- Manual guiado.
- Validaciones de correo y contrasena.
- Servicio `authService` conectado a `/auth` y `/users`.

## Gestion de proyectos y colaboracion

Implementado en `frontend/src/modules/gestion_proyectos_colaboracion/`.

- Listado de proyectos.
- Creacion de proyectos.
- Archivado de proyectos.
- Entorno de proyecto.
- Listado de integrantes.
- Creacion de diagramas desde el proyecto.
- Guardado de versiones.
- Estado global de proyecto activo.

## Modelado UML inteligente

Implementado en `frontend/src/modules/modelado_uml_inteligente/`.

- Editor UML inicial con React Flow.
- Nodo visual de clase UML con nombre, atributos y metodos.
- Toolbar con acciones de clase, validacion, importacion, exportacion e imagen a UML.
- Panel lateral de propiedades.
- Validacion del diagrama mediante backend.
- Eventos WebSocket para cambios UML colaborativos.

## Transformacion y generacion automatica de software

Implementado en `frontend/src/modules/transformacion_generacion_software/`.

- Formulario de transformacion UML.
- Ejecucion de modelo intermedio.
- Generacion backend Spring Boot.
- Generacion frontend Flutter.
- Visualizacion de estado y artefactos generados.
