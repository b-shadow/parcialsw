# PROMPT FASE 4: DESARROLLO DEL BACKEND PRINCIPAL PYTHON + FASTAPI CON ARQUITECTURA MODULAR POR PAQUETES FUNCIONALES

## Contexto general de la fase

Esta fase corresponde al desarrollo del backend principal de la
plataforma CASE inteligente y colaborativa.

El backend principal será desarrollado utilizando:

-   Python 3.12.
-   FastAPI.
-   SQLAlchemy.
-   PostgreSQL.
-   WebSockets.

Este backend será responsable de administrar la plataforma web CASE,
permitiendo la creación colaborativa de diagramas UML, gestión de
proyectos y preparación de los procesos de generación automática de
software.

Es importante diferenciar este backend del software generado
automáticamente:

-   Backend principal:
    -   Python + FastAPI.
    -   Administra la plataforma CASE.
-   Backend generado:
    -   Spring Boot.
    -   Se crea automáticamente a partir del modelo UML.

La arquitectura del backend debe ser estrictamente modular, pero los
módulos deben corresponder directamente a los cuatro paquetes
funcionales definidos durante el análisis del sistema.

No se debe crear una separación arbitraria por componentes técnicos,
sino una separación basada en los dominios funcionales del sistema.

------------------------------------------------------------------------

# Objetivo general de la fase

Implementar el backend principal utilizando una arquitectura modular
basada en los cuatro paquetes principales del sistema:

1.  Gestión de acceso, usuarios y seguimiento.
2.  Gestión de proyectos y colaboración.
3.  Modelado UML inteligente.
4.  Transformación y generación automática de software.

Cada módulo debe contener sus propios componentes internos:

-   Modelos.
-   Esquemas.
-   Servicios.
-   Repositorios.
-   Controladores.
-   Validaciones.

La comunicación entre módulos debe realizarse mediante interfaces claras
para mantener bajo acoplamiento.

------------------------------------------------------------------------

# 1. Arquitectura modular general

La estructura del backend debe organizarse de la siguiente manera:

    backend/

    ├── app/

    │   ├── core/

    │   │   ├── config/

    │   │   ├── database/

    │   │   ├── security/

    │   │   └── middleware/

    │   │

    │   ├── modules/

    │   │

    │   │   ├── acceso_usuarios/

    │   │   │
    │   │   ├── proyectos_colaboracion/

    │   │   │
    │   │   ├── modelado_uml/

    │   │   │
    │   │   └── generacion_software/

    │   │

    │   ├── websocket/

    │   │

    │   └── main.py

    └── migrations/

Cada módulo debe ser independiente y contener:

    modulo/

    ├── models/

    ├── schemas/

    ├── repositories/

    ├── services/

    ├── routers/

    ├── validators/

    └── tests/

------------------------------------------------------------------------

# 2. Módulo 1: Gestión de acceso, usuarios y seguimiento

## Objetivo del módulo

Administrar la identidad de los usuarios, autenticación, roles globales,
perfiles, reportes y bitácora.

Casos de uso relacionados:

-   CU-01 Gestionar cuenta de usuario.
-   CU-02 Gestionar usuarios y roles globales.
-   CU-03 Consultar reportes del proyecto.
-   CU-04 Consultar bitácora del proyecto.
-   CU-05 Consultar manual de usuario guiado.

------------------------------------------------------------------------

## Funcionalidades a implementar

### Gestión de usuarios

Implementar:

-   Registro de usuarios.
-   Consulta de usuarios.
-   Actualización de información.
-   Activación y desactivación.

------------------------------------------------------------------------

### Autenticación

Implementar:

-   Inicio de sesión.
-   Cierre de sesión.
-   Manejo de tokens.
-   Recuperación de acceso.

Tecnología:

-   JWT.

------------------------------------------------------------------------

### Roles globales

Gestionar:

-   Administrador.
-   Editor.
-   Organizador.

Diferenciar:

Rol global:

Define permisos generales del sistema.

Rol interno:

Define participación dentro de un proyecto.

------------------------------------------------------------------------

### Perfil de usuario

Implementar:

-   Consulta de perfil.
-   Modificación de información.
-   Preferencias personales.

------------------------------------------------------------------------

### Bitácora

Registrar:

-   Accesos.
-   Cambios realizados.
-   Acciones administrativas.
-   Eventos importantes.

------------------------------------------------------------------------

# 3. Módulo 2: Gestión de proyectos y colaboración

## Objetivo del módulo

Administrar espacios colaborativos donde los usuarios trabajan sobre
diagramas UML y procesos de generación.

Casos de uso relacionados:

-   CU-06 Gestionar proyectos de desarrollo.
-   CU-07 Gestionar integrantes y permisos del proyecto.
-   CU-08 Gestionar versiones y cambios del proyecto.
-   CU-09 Sincronizar proyectos con plataforma cloud.

------------------------------------------------------------------------

## Funcionalidades a implementar

### Gestión de proyectos

Implementar:

-   Crear proyecto.
-   Modificar proyecto.
-   Consultar proyectos.
-   Eliminar proyecto.

Regla de negocio:

Cuando un Editor crea un proyecto:

-   Se convierte automáticamente en Organizador de dicho proyecto.

------------------------------------------------------------------------

### Integrantes del proyecto

Implementar:

-   Invitaciones.
-   Agregar integrantes.
-   Retirar integrantes.
-   Gestión de permisos.

Roles internos:

-   Organizador.
-   Editor.

------------------------------------------------------------------------

### Versionamiento

Implementar:

-   Crear versión.
-   Guardar cambios.
-   Consultar historial.
-   Restaurar versiones.

------------------------------------------------------------------------

### Colaboración en tiempo real

Implementar mediante WebSockets.

Debe permitir:

-   Usuarios conectados al proyecto.
-   Sincronización de cambios.
-   Actualización instantánea del diagrama.

------------------------------------------------------------------------

# 4. Módulo 3: Modelado UML inteligente

## Objetivo del módulo

Administrar la creación, edición, validación e intercambio de diagramas
de clases UML.

Casos de uso relacionados:

-   CU-10 Crear y editar diagramas de clases UML.
-   CU-11 Generar diagramas de clases UML mediante procesamiento de
    imágenes.
-   CU-12 Importar y exportar modelos UML.
-   CU-13 Validar diagramas de clases UML.

------------------------------------------------------------------------

## Funcionalidades a implementar

### Gestión del modelo UML

Implementar:

-   Crear diagramas.
-   Modificar diagramas.
-   Guardar elementos UML.

------------------------------------------------------------------------

### Elementos UML

Gestionar:

-   Clases.
-   Atributos.
-   Métodos.
-   Relaciones.
-   Herencia.
-   Interfaces.

------------------------------------------------------------------------

### Editor colaborativo

Preparar comunicación con:

-   Frontend React.
-   WebSockets.

Eventos:

-   Crear clase.
-   Modificar clase.
-   Eliminar clase.
-   Crear relación.
-   Actualizar posición.

------------------------------------------------------------------------

### Validación UML

Implementar servicios para:

-   Detectar inconsistencias.
-   Revisar relaciones.
-   Validar estructura.

------------------------------------------------------------------------

### Importación y exportación

Preparar:

-   Exportación XMI.
-   Importación XMI.
-   Compatibilidad con Enterprise Architect.

------------------------------------------------------------------------

# 5. Módulo 4: Transformación y generación automática de software

## Objetivo del módulo

Transformar modelos UML en aplicaciones funcionales.

Casos de uso relacionados:

-   CU-14 Transformar modelo UML a estructura de implementación.
-   CU-15 Generar backend Spring Boot.
-   CU-16 Generar frontend móvil Flutter.
-   CU-17 Ejecutar generación mediante IA local offline.

------------------------------------------------------------------------

## Funcionalidades a implementar

### Transformación UML

Implementar:

-   Interpretación de clases.
-   Interpretación de atributos.
-   Interpretación de métodos.
-   Interpretación de relaciones.

Preparar estructura intermedia para generación.

------------------------------------------------------------------------

### Generador backend Spring Boot

Preparar servicios para:

-   Crear proyecto Spring Boot.
-   Generar entidades JPA.
-   Generar repositorios.
-   Generar servicios.
-   Generar controladores.
-   Generar CRUD.

------------------------------------------------------------------------

### Generador frontend Flutter

Preparar servicios para:

-   Generar modelos.
-   Generar pantallas.
-   Generar formularios.
-   Generar consumo API.

------------------------------------------------------------------------

### Integración IA local

Preparar comunicación con:

-   Modelo IA offline.
-   Procesamiento de texto.
-   Procesamiento de voz.
-   Procesamiento de imágenes.

------------------------------------------------------------------------

# 6. Comunicación entre módulos

Definir mecanismos de comunicación.

Ejemplos:

Módulo proyectos:

solicita información al módulo UML.

Módulo UML:

envía modelo al módulo generación.

Módulo generación:

produce código.

Debe evitarse dependencia directa entre módulos.

------------------------------------------------------------------------

# 7. Base de datos y ORM

Cada módulo debe administrar sus modelos SQLAlchemy correspondientes.

Ejemplo:

    modules/

    acceso_usuarios/models/

    proyectos_colaboracion/models/

    modelado_uml/models/

    generacion_software/models/

------------------------------------------------------------------------

# 8. Seguridad

Implementar:

-   Autenticación.
-   Autorización.
-   Validación de permisos.
-   Protección de endpoints.

Controlar:

-   Administrador.
-   Editor.
-   Organizador.

------------------------------------------------------------------------

# 9. Pruebas

Realizar:

## Pruebas unitarias

Por módulo.

## Pruebas integración

Entre módulos.

## Pruebas WebSocket

Validar:

-   Múltiples usuarios.
-   Sincronización.
-   Persistencia.

------------------------------------------------------------------------

# 10. Documentación técnica

Generar:

-   Arquitectura modular.
-   Estructura backend.
-   Documentación API.
-   Swagger.
-   Manual ejecución.

------------------------------------------------------------------------

# Entregables de la fase

-   Backend FastAPI modular funcional.
-   Cuatro módulos principales implementados.
-   Integración PostgreSQL.
-   APIs REST.
-   WebSockets.
-   Seguridad.
-   Documentación técnica.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
