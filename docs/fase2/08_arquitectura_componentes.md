# Fase 2 - Arquitectura de componentes

## Componentes por paquete funcional

### Gestion de acceso, usuarios y seguimiento

Frontend:

- Pantallas de login, registro y perfil.
- Panel de usuarios para Administrador.
- Panel de reportes.
- Manual guiado.

Backend:

- Router de autenticacion.
- Servicio de usuarios.
- Servicio de roles.
- Servicio JWT.
- Servicio de bitacora.
- Repositorios de usuarios, roles, sesiones y auditoria.

Datos:

- Usuarios.
- Roles globales.
- Sesiones.
- Bitacora.

### Gestion de proyectos y colaboracion

Frontend:

- Listado de proyectos.
- Formulario de proyecto.
- Administracion de integrantes.
- Historial de versiones.
- Estado de usuarios conectados.

Backend:

- Router de proyectos.
- Servicio de integrantes.
- Servicio de permisos internos.
- Servicio de versiones.
- WebSocket manager.
- Repositorios de proyectos, integrantes, permisos, versiones y eventos.

Datos:

- Proyectos.
- Integrantes.
- Permisos internos.
- Versiones.
- Eventos colaborativos.

### Modelado UML inteligente

Frontend:

- Canvas UML.
- Nodos de clase.
- Relaciones.
- Barra de herramientas.
- Panel de propiedades.
- Panel de validacion.
- Importador/exportador XMI.

Backend:

- Router UML.
- Servicio de diagramas.
- Servicio de elementos UML.
- Servicio de validacion.
- Servicio XMI.
- Servicio de eventos UML.

Datos:

- Diagramas.
- Clases UML.
- Atributos.
- Metodos.
- Relaciones.
- Posiciones visuales.

### Transformacion y generacion automatica

Frontend:

- Panel de transformacion.
- Configuracion de generacion Spring Boot.
- Configuracion de generacion Flutter.
- Visor de progreso.
- Descarga de artefactos.

Backend:

- Router de generacion.
- Servicio de transformacion UML.
- Servicio generador Spring Boot.
- Servicio generador Flutter.
- Servicio de artefactos.
- Repositorio de procesos y resultados.

Datos:

- Transformaciones.
- Procesos de generacion.
- Artefactos backend.
- Artefactos frontend.
- Logs de generacion.

## Integracion entre componentes

- Acceso/usuarios provee identidad y permisos a los demas modulos.
- Proyectos/colaboracion define el contexto de trabajo.
- Modelado UML administra el modelo fuente.
- Generacion consume el modelo UML validado.
- IA asiste a Modelado UML y Generacion.
- Bitacora recibe eventos de todos los modulos.

