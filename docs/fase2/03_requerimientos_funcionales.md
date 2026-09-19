# Fase 2 - Requerimientos funcionales

## Modulo 1: Gestion de acceso, usuarios y seguimiento

| ID | Requerimiento | Prioridad |
| --- | --- | --- |
| RF-01 | Permitir registro de usuarios con nombre, correo y contrasena cifrada. | Alta |
| RF-02 | Permitir inicio de sesion mediante credenciales validas. | Alta |
| RF-03 | Emitir y validar tokens JWT para sesiones autenticadas. | Alta |
| RF-04 | Permitir cierre de sesion e invalidacion logica de sesion. | Media |
| RF-05 | Permitir consulta y modificacion de perfil propio. | Media |
| RF-06 | Permitir al Administrador listar usuarios. | Alta |
| RF-07 | Permitir al Administrador activar o desactivar usuarios. | Alta |
| RF-08 | Permitir gestion de roles globales Administrador, Editor y Organizador. | Alta |
| RF-09 | Registrar acciones relevantes en bitacora. | Alta |
| RF-10 | Permitir consulta de reportes administrativos y de proyecto. | Media |
| RF-11 | Proveer manual guiado y ayuda contextual. | Media |

## Modulo 2: Gestion de proyectos y colaboracion

| ID | Requerimiento | Prioridad |
| --- | --- | --- |
| RF-12 | Permitir crear proyectos de desarrollo. | Alta |
| RF-13 | Asignar automaticamente rol Organizador interno al creador del proyecto. | Alta |
| RF-14 | Permitir consultar proyectos propios y compartidos. | Alta |
| RF-15 | Permitir modificar informacion general del proyecto. | Media |
| RF-16 | Permitir eliminar o archivar proyectos segun permisos. | Media |
| RF-17 | Permitir invitar integrantes al proyecto. | Alta |
| RF-18 | Permitir aceptar o rechazar invitaciones. | Media |
| RF-19 | Permitir asignar permisos internos de proyecto. | Alta |
| RF-20 | Permitir retirar integrantes. | Alta |
| RF-21 | Permitir crear versiones del modelo del proyecto. | Alta |
| RF-22 | Permitir consultar historial de cambios. | Alta |
| RF-23 | Permitir restaurar versiones previas. | Media |
| RF-24 | Permitir conexion colaborativa en tiempo real por proyecto. | Alta |
| RF-25 | Sincronizar eventos UML entre usuarios conectados. | Alta |

## Modulo 3: Modelado UML inteligente

| ID | Requerimiento | Prioridad |
| --- | --- | --- |
| RF-26 | Permitir crear diagramas de clases UML. | Alta |
| RF-27 | Permitir crear, editar, mover y eliminar clases UML. | Alta |
| RF-28 | Permitir crear, editar y eliminar atributos UML. | Alta |
| RF-29 | Permitir crear, editar y eliminar metodos UML. | Alta |
| RF-30 | Permitir crear, editar y eliminar relaciones UML. | Alta |
| RF-31 | Soportar asociacion, herencia, implementacion, dependencia, agregacion y composicion. | Alta |
| RF-32 | Guardar posiciones visuales de elementos. | Alta |
| RF-33 | Validar estructura UML y reportar errores. | Alta |
| RF-34 | Generar recomendaciones de mejora de diseno. | Media |
| RF-35 | Generar diagramas desde instrucciones de texto. | Alta |
| RF-36 | Generar diagramas desde comandos de voz convertidos a texto. | Media |
| RF-37 | Reconstruir modelos UML desde imagenes. | Alta |
| RF-38 | Importar modelos XMI. | Media |
| RF-39 | Exportar modelos XMI compatibles. | Media |

## Modulo 4: Transformacion y generacion automatica de software

| ID | Requerimiento | Prioridad |
| --- | --- | --- |
| RF-40 | Transformar UML en estructura intermedia de implementacion. | Alta |
| RF-41 | Generar backend Spring Boot desde clases UML. | Alta |
| RF-42 | Generar entidades JPA y relaciones. | Alta |
| RF-43 | Generar DTO, repositorios, servicios y controladores REST. | Alta |
| RF-44 | Generar validaciones y manejo basico de excepciones. | Alta |
| RF-45 | Generar configuracion Spring Security/JWT inicial. | Media |
| RF-46 | Generar frontend Flutter desde UML y contratos backend. | Alta |
| RF-47 | Generar modelos Dart, servicios API, pantallas CRUD y formularios. | Alta |
| RF-48 | Registrar procesos de generacion. | Alta |
| RF-49 | Exportar proyectos generados como ZIP o artefacto descargable. | Media |
| RF-50 | Comparar generaciones/versiones generadas. | Media |

