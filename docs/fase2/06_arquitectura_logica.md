# Fase 2 - Arquitectura logica

## Vista general

La arquitectura logica separa responsabilidades por productos y por dominios funcionales. El backend FastAPI coordina reglas, persistencia, seguridad, colaboracion, IA y generacion. El frontend React presenta las interfaces por modulo. El motor IA y los generadores se integran mediante contratos internos.

## Frontend React

Componentes logicos:

- Autenticacion y sesion.
- Gestion de usuarios y perfil.
- Administracion de proyectos.
- Gestion de integrantes y permisos.
- Editor UML.
- Panel de propiedades UML.
- Panel de IA.
- Importacion/exportacion XMI.
- Panel de transformacion y generacion.
- Reportes y bitacora.

Organizacion:

- `core`: API, rutas, autenticacion, configuracion y WebSockets.
- `modules`: dominios funcionales.
- `shared`: componentes, layouts, hooks, utilidades e iconos.

## Backend FastAPI

Componentes logicos:

- `core/config`: configuracion.
- `core/database`: conexion y sesiones SQLAlchemy.
- `core/security`: JWT, hashing, autorizacion.
- `core/middleware`: CORS, auditoria y manejo transversal.
- `modules/acceso_usuarios`: usuarios, roles, autenticacion, reportes y bitacora.
- `modules/proyectos_colaboracion`: proyectos, integrantes, permisos, versiones y sesiones.
- `modules/modelado_uml`: diagramas, clases, atributos, metodos, relaciones, XMI y validacion.
- `modules/generacion_software`: transformacion UML, generacion Spring Boot, generacion Flutter y registro de artefactos.
- `websocket`: canales colaborativos por proyecto.

## Motor UML

Responsabilidades:

- Mantener modelo interno independiente del canvas.
- Representar diagramas de clases.
- Representar clases, atributos, metodos y relaciones.
- Validar reglas estructurales.
- Emitir y consumir eventos colaborativos.
- Exportar/importar representaciones XMI.
- Entregar estructura compatible con generadores.

## Motor IA local offline

Responsabilidades:

- Convertir instrucciones de texto a UML.
- Procesar texto derivado de voz.
- Interpretar imagenes de diagramas.
- Validar modelos y proponer mejoras.
- Asistir procesos de transformacion/generacion.

Restriccion:

- Debe funcionar sin dependencia final de APIs externas.

## Generador Spring Boot

Responsabilidades:

- Parsear modelo UML interno.
- Analizar entidades y relaciones.
- Aplicar reglas UML a Java/JPA.
- Generar proyecto Spring Boot con CRUD.
- Validar estructura y registrar resultado.

## Generador Flutter

Responsabilidades:

- Analizar modelo UML y contratos backend.
- Generar modelos Dart.
- Generar servicios API.
- Generar pantallas CRUD, formularios y navegacion.
- Validar estructura y registrar resultado.

