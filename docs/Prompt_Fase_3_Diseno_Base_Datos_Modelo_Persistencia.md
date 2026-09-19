# PROMPT FASE 3: DISEÑO COMPLETO DE BASE DE DATOS Y MODELO DE PERSISTENCIA

## Contexto general de la fase

Esta fase corresponde al diseño completo de la base de datos del sistema
CASE inteligente y colaborativo.

El objetivo es transformar los requerimientos funcionales definidos
previamente en un modelo de información estructurado que permita
almacenar toda la información necesaria para el funcionamiento de la
plataforma.

La base de datos debe soportar:

-   Gestión de usuarios.
-   Gestión de roles globales.
-   Gestión de proyectos colaborativos.
-   Administración de integrantes y permisos internos.
-   Almacenamiento de diagramas de clases UML.
-   Persistencia del modelo UML.
-   Versionamiento de cambios.
-   Registro de eventos colaborativos.
-   Bitácora del proyecto.
-   Reportes.
-   Importación y exportación de modelos UML.
-   Procesos de generación automática de software.
-   Registro de backend generado.
-   Registro de frontend generado.
-   Información relacionada con IA y procesos ejecutados.

La base de datos utilizará:

-   PostgreSQL como sistema gestor principal.
-   SQLAlchemy como ORM del backend Python.
-   Alembic para control de migraciones.

------------------------------------------------------------------------

# Objetivo general de la fase

Diseñar la arquitectura de datos completa del sistema mediante:

-   Identificación de entidades.
-   Modelo conceptual.
-   Modelo lógico.
-   Normalización.
-   Modelo físico.
-   Definición de relaciones.
-   Restricciones.
-   Índices.
-   Consideraciones de rendimiento.
-   Preparación para implementación.

------------------------------------------------------------------------

# 1. Análisis de información requerida por el sistema

Realizar un análisis de todos los datos que el sistema necesita
administrar.

Debe considerar los cuatro paquetes funcionales:

------------------------------------------------------------------------

# Paquete 1: Gestión de acceso, usuarios y seguimiento

Analizar las entidades necesarias para:

-   Registro de usuarios.
-   Autenticación.
-   Perfil personal.
-   Roles globales.
-   Reportes.
-   Bitácora.
-   Manual guiado.

Identificar información como:

## Usuarios

Datos necesarios:

-   Identificador.
-   Nombre.
-   Correo electrónico.
-   Contraseña cifrada.
-   Estado.
-   Fecha de creación.
-   Último acceso.

------------------------------------------------------------------------

## Roles globales

Considerar:

-   Administrador.
-   Editor.
-   Organizador.

Definir si serán roles globales o permisos asociados.

------------------------------------------------------------------------

## Sesiones

Analizar almacenamiento de:

-   Inicio de sesión.
-   Cierre de sesión.
-   Tokens.
-   Sesiones activas.

------------------------------------------------------------------------

## Bitácora

Definir información:

-   Usuario.
-   Acción realizada.
-   Fecha.
-   Proyecto relacionado.
-   Módulo afectado.

------------------------------------------------------------------------

# Paquete 2: Gestión de proyectos y colaboración

Diseñar las entidades necesarias para soportar trabajo colaborativo.

------------------------------------------------------------------------

# Entidad Proyecto

Debe almacenar:

-   Información general.
-   Propietario inicial.
-   Estado.
-   Fechas.
-   Configuración.

Analizar:

-   Un usuario puede crear múltiples proyectos.
-   Un proyecto pertenece a un organizador.
-   Un proyecto tiene múltiples integrantes.

------------------------------------------------------------------------

# Integrantes del proyecto

Diseñar relación entre:

Usuario ↔ Proyecto

Debe permitir:

-   Agregar integrantes.
-   Retirar integrantes.
-   Asignar permisos internos.

Roles dentro del proyecto:

-   Organizador.
-   Editor.

Considerar diferencia entre:

Rol global:

Administrador.

Rol interno:

Organizador o Editor dentro de un proyecto específico.

------------------------------------------------------------------------

# Permisos del proyecto

Analizar si requiere entidad propia.

Debe permitir controlar:

-   Editar UML.
-   Generar código.
-   Gestionar integrantes.
-   Exportar modelos.
-   Consultar reportes.

------------------------------------------------------------------------

# Versionamiento del proyecto

Diseñar almacenamiento para:

-   Versiones.
-   Fecha.
-   Usuario creador.
-   Descripción del cambio.
-   Estado.

------------------------------------------------------------------------

# Colaboración en tiempo real

Considerar persistencia relacionada con WebSockets.

Diseñar almacenamiento para:

-   Sesiones colaborativas.
-   Usuarios conectados.
-   Eventos enviados.
-   Cambios realizados.

Analizar implementación mediante:

-   Registro de eventos.
-   Historial de modificaciones.

------------------------------------------------------------------------

# Paquete 3: Modelado UML inteligente

Este es uno de los módulos principales.

La base de datos debe representar un modelo UML completo.

------------------------------------------------------------------------

# Modelo UML principal

Diseñar entidades para:

## Diagrama

Debe almacenar:

-   Identificador.
-   Proyecto asociado.
-   Nombre.
-   Tipo.
-   Fecha creación.
-   Estado.

------------------------------------------------------------------------

# Clase UML

Debe representar:

-   Nombre.
-   Visibilidad.
-   Tipo.
-   Ubicación gráfica.
-   Posición dentro del editor.

------------------------------------------------------------------------

# Atributo UML

Debe almacenar:

-   Nombre.
-   Tipo de dato.
-   Visibilidad.
-   Valor inicial.

------------------------------------------------------------------------

# Método UML

Debe almacenar:

-   Nombre.
-   Tipo retorno.
-   Parámetros.
-   Visibilidad.

------------------------------------------------------------------------

# Relaciones UML

Diseñar entidad para:

-   Asociación.
-   Herencia.
-   Implementación.
-   Dependencia.

Debe almacenar:

-   Clase origen.
-   Clase destino.
-   Tipo relación.
-   Cardinalidad.

------------------------------------------------------------------------

# Elementos gráficos del editor

Analizar almacenamiento de:

-   Coordenadas.
-   Tamaño.
-   Posición.
-   Configuración visual.

Esto permitirá reconstruir el diagrama exactamente.

------------------------------------------------------------------------

# Modelos importados y exportados

Diseñar entidades para:

-   Archivos XMI.
-   Fecha importación.
-   Fecha exportación.
-   Herramienta origen.
-   Herramienta destino.

Considerar:

-   Enterprise Architect.
-   Otros sistemas UML compatibles.

------------------------------------------------------------------------

# Paquete 4: Transformación y generación automática de software

Diseñar entidades relacionadas con la generación.

------------------------------------------------------------------------

# Transformación UML

Registrar:

-   Modelo utilizado.
-   Fecha.
-   Usuario.
-   Resultado.
-   Estado.

------------------------------------------------------------------------

# Backend generado

Almacenar:

-   Proyecto generado.
-   Versión.
-   Tecnología.
-   Fecha.
-   Usuario.
-   Estado.

Información posible:

-   Spring Boot.
-   Java.
-   PostgreSQL.
-   Hibernate.

------------------------------------------------------------------------

# Frontend generado

Almacenar:

-   Proyecto generado.
-   Tecnología.
-   Versión.
-   Fecha.

Información:

-   Flutter.
-   Dart.
-   Componentes generados.

------------------------------------------------------------------------

# Procesos IA

Diseñar entidades para registrar:

-   Solicitud realizada.
-   Tipo de IA utilizada.
-   Entrada.
-   Resultado.
-   Fecha.
-   Usuario.

Tipos:

-   Texto a UML.
-   Voz a UML.
-   Imagen a UML.
-   Validación.
-   Generación código.

------------------------------------------------------------------------

# 2. Modelo conceptual de base de datos

Crear el modelo conceptual.

Debe incluir:

-   Entidades principales.
-   Relaciones.
-   Cardinalidades.

Representar mediante:

-   Diagrama entidad relación.
-   Descripción de entidades.

No considerar todavía atributos técnicos.

------------------------------------------------------------------------

# 3. Modelo lógico de base de datos

Transformar el modelo conceptual a tablas.

Para cada tabla definir:

-   Nombre.
-   Propósito.
-   Clave primaria.
-   Claves foráneas.
-   Atributos.
-   Restricciones.

------------------------------------------------------------------------

# 4. Normalización

Aplicar normalización desde el punto de vista de consistencia.

Realizar:

## Primera forma normal (1FN)

Verificar:

-   Campos atómicos.
-   Sin grupos repetitivos.

------------------------------------------------------------------------

## Segunda forma normal (2FN)

Verificar:

-   Dependencia completa de claves.

------------------------------------------------------------------------

## Tercera forma normal (3FN)

Verificar:

-   Eliminación de dependencias transitivas.
-   Evitar redundancia.

------------------------------------------------------------------------

# 5. Modelo físico PostgreSQL

Definir implementación real.

Para cada tabla especificar:

-   Nombre físico.
-   Tipo de dato PostgreSQL.
-   Restricciones.
-   Índices.
-   Relaciones.

Considerar:

Tipos:

-   UUID.
-   VARCHAR.
-   TEXT.
-   BOOLEAN.
-   TIMESTAMP.
-   JSONB.

------------------------------------------------------------------------

# 6. Consideraciones especiales del sistema

## Almacenamiento de modelos UML

Evaluar estrategia:

Opción híbrida:

-   Tablas normalizadas para elementos UML.
-   JSONB para configuraciones dinámicas.

Justificar decisión.

------------------------------------------------------------------------

## Versionamiento

Definir:

-   Cómo almacenar versiones.
-   Cómo recuperar estados anteriores.
-   Cómo comparar cambios.

------------------------------------------------------------------------

## Eventos colaborativos

Definir:

-   Registro de eventos.
-   Usuario responsable.
-   Momento del cambio.
-   Elemento afectado.

------------------------------------------------------------------------

## Seguridad

Definir:

-   Cifrado de contraseñas.
-   Restricciones de acceso.
-   Separación de permisos.

------------------------------------------------------------------------

# 7. Preparación para implementación con SQLAlchemy

Definir:

-   Modelos ORM.
-   Relaciones.
-   Entidades principales.
-   Estructura del paquete database.

Ejemplo:

    backend/
     └── models/
          ├── usuario.py
          ├── proyecto.py
          ├── uml.py
          ├── generacion.py
          └── auditoria.py

------------------------------------------------------------------------

# 8. Scripts iniciales de base de datos

Generar:

-   Creación de tablas.
-   Restricciones.
-   Índices.
-   Datos iniciales.

Considerar:

Datos base:

-   Roles globales.
-   Permisos iniciales.

------------------------------------------------------------------------

# 9. Diagramas necesarios

Generar:

-   Modelo entidad relación.
-   Modelo lógico.
-   Modelo físico.
-   Diagrama de clases del modelo de datos.
-   Diagrama de relaciones UML almacenadas.

------------------------------------------------------------------------

# 10. Entregables de la fase

La fase debe entregar:

-   Documento de diseño de base de datos.
-   Modelo conceptual.
-   Modelo lógico.
-   Modelo físico.
-   Normalización.
-   Diccionario de datos.
-   Script PostgreSQL.
-   Modelo ORM inicial.
-   Diagramas correspondientes.

------------------------------------------------------------------------

# Casos de uso relacionados

Los casos de uso considerados para el diseño de datos son:

-   CU-01 Registrar cuenta de usuario.
-   CU-02 Gestionar autenticación.
-   CU-03 Gestionar perfil propio.
-   CU-04 Gestionar usuarios y roles globales.
-   CU-05 Consultar reportes del proyecto.
-   CU-06 Consultar bitácora del proyecto.
-   CU-08 Gestionar proyectos de desarrollo.
-   CU-09 Gestionar integrantes y permisos del proyecto.
-   CU-10 Gestionar versiones y cambios del proyecto.
-   CU-11 Crear y editar diagramas de clases UML.
-   CU-12 Generar diagramas de clases UML mediante procesamiento de
    imágenes.
-   CU-13 Importar y exportar modelos UML.
-   CU-14 Validar diagramas de clases UML.
-   CU-15 Transformar modelo UML a estructura de implementación.
-   CU-16 Generar backend Spring Boot.
-   CU-17 Generar frontend móvil Flutter.
-   CU-18 Ejecutar generación mediante IA local offline.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
