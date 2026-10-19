# PROMPT FASE 1: INICIACIÓN DEL PROYECTO, ARQUITECTURA TECNOLÓGICA Y DEFINICIÓN DE HERRAMIENTAS

## Contexto general del proyecto

Se debe iniciar el desarrollo de una plataforma CASE inteligente y
colaborativa orientada al modelado UML y generación automática de
software.

El sistema no será un simple diagramador, sino una plataforma capaz de:

-   Crear y editar diagramas de clases UML.
-   Permitir trabajo colaborativo en tiempo real entre múltiples
    usuarios.
-   Recibir instrucciones mediante texto y voz.
-   Procesar imágenes de diagramas UML para reconstruir modelos.
-   Importar y exportar modelos UML mediante estándares como XMI.
-   Integrarse con herramientas externas como Enterprise Architect.
-   Validar modelos UML mediante inteligencia artificial.
-   Transformar diagramas de clases UML en código funcional.
-   Generar automáticamente backend Spring Boot.
-   Generar automáticamente frontend móvil Flutter.
-   Ejecutar capacidades inteligentes mediante modelos de IA locales sin
    conexión a internet.

La arquitectura general debe considerar tres productos principales:

1.  Plataforma CASE colaborativa web.
2.  Motor inteligente de análisis y generación.
3.  Motor de generación automática de software.

------------------------------------------------------------------------

# Objetivo de la Fase 1

Definir completamente la base tecnológica, arquitectura general,
herramientas, frameworks, librerías y criterios técnicos que serán
utilizados durante todo el desarrollo del proyecto.

Esta fase no implementa todavía funcionalidades completas, sino que
establece la arquitectura sobre la cual se construirán todas las fases
posteriores.

------------------------------------------------------------------------

# 1. Análisis inicial del sistema

Realizar un análisis general del problema identificando:

-   Alcance del sistema.
-   Componentes principales.
-   Usuarios involucrados.
-   Flujo general de funcionamiento.
-   Dependencias tecnológicas.
-   Restricciones del proyecto.

Definir claramente que la plataforma funcionará bajo el siguiente flujo:

Usuario crea o importa un modelo UML.

↓

Sistema analiza y almacena el modelo.

↓

Usuarios colaboran sobre el mismo diagrama en tiempo real.

↓

IA interpreta instrucciones, imágenes o voz.

↓

Modelo UML validado.

↓

Sistema transforma UML a estructura de implementación.

↓

Sistema genera backend Spring Boot.

↓

Sistema genera frontend Flutter.

↓

Sistema permite ejecución mediante IA local offline.

------------------------------------------------------------------------

# 2. Definición de arquitectura general

Diseñar la arquitectura global del sistema considerando una arquitectura
distribuida.

La solución estará compuesta por:

## Frontend principal web

Tecnología:

-   React.
-   TypeScript.
-   Vite.

Responsabilidades:

-   Interfaz gráfica.
-   Gestión de usuarios.
-   Gestión de proyectos.
-   Editor UML.
-   Visualización colaborativa.
-   Comunicación con WebSockets.
-   Interacción con módulos de IA.

------------------------------------------------------------------------

## Backend principal de plataforma

Tecnología:

-   Python 3.12.
-   FastAPI.

Responsabilidades:

-   API REST.
-   Autenticación.
-   Gestión usuarios.
-   Gestión proyectos.
-   Gestión permisos.
-   Gestión modelos UML.
-   Comunicación con base de datos.
-   Servicios inteligentes.
-   Comunicación WebSocket.

------------------------------------------------------------------------

## Comunicación en tiempo real

Definir arquitectura colaborativa mediante:

-   WebSockets.
-   Socket.IO.

Debe permitir:

-   Usuarios conectados simultáneamente.
-   Actualización instantánea del diagrama.
-   Sincronización de cambios.
-   Eventos colaborativos.
-   Control de sesiones.

Definir eventos principales:

-   Usuario conectado.
-   Usuario desconectado.
-   Crear clase.
-   Modificar clase.
-   Eliminar clase.
-   Crear relación.
-   Modificar atributo.
-   Guardar versión.
-   Restaurar versión.

------------------------------------------------------------------------

## Base de datos

Tecnología:

-   PostgreSQL.

Responsabilidad:

Almacenar:

-   Usuarios.
-   Roles.
-   Proyectos.
-   Integrantes.
-   Permisos.
-   Diagramas UML.
-   Versiones.
-   Cambios.
-   Bitácora.
-   Procesos de generación.

------------------------------------------------------------------------

## Infraestructura

Definir despliegue mediante:

-   AWS.

Considerar:

-   Servidor backend.
-   Base de datos.
-   Almacenamiento.
-   Servicios auxiliares.
-   Seguridad.
-   Escalabilidad.

------------------------------------------------------------------------

# 3. Definición de librerías frontend React

Seleccionar librerías compatibles y justificar su uso.

## React Flow

Uso:

Será la librería principal para el editor visual UML.

Permite:

-   Crear nodos.
-   Crear conexiones.
-   Manipular elementos gráficos.
-   Mover componentes.
-   Construir diagramas interactivos.

Debe evaluarse su adaptación para:

-   Clases UML.
-   Relaciones.
-   Herencia.
-   Interfaces.

------------------------------------------------------------------------

## Material UI

Uso:

Sistema de componentes visuales.

Aplicación:

-   Formularios.
-   Paneles.
-   Menús.
-   Modales.
-   Configuraciones.

------------------------------------------------------------------------

## React Icons

Uso:

Sistema de iconografía.

Aplicación:

-   Herramientas UML.
-   Menús.
-   Botones.
-   Acciones.

------------------------------------------------------------------------

## Zustand

Uso:

Administración del estado global.

Debe manejar:

-   Usuario autenticado.
-   Proyecto actual.
-   Modelo UML activo.
-   Cambios pendientes.
-   Estado colaboración.

------------------------------------------------------------------------

## Axios

Uso:

Comunicación HTTP con backend FastAPI.

------------------------------------------------------------------------

## Socket.IO Client

Uso:

Comunicación colaborativa en tiempo real.

Debe manejar:

-   Conexión a salas.
-   Eventos UML.
-   Actualizaciones del modelo.

------------------------------------------------------------------------

# 4. Definición de librerías backend Python

## FastAPI

Framework principal.

Uso:

-   API REST.
-   WebSockets.
-   Servicios internos.

------------------------------------------------------------------------

## SQLAlchemy

Uso:

ORM para PostgreSQL.

Debe permitir:

-   Modelado de entidades.
-   Consultas.
-   Relaciones.
-   Persistencia.

------------------------------------------------------------------------

## Alembic

Uso:

Migraciones de base de datos.

------------------------------------------------------------------------

## Pydantic

Uso:

Validación de datos.

Aplicación:

-   Solicitudes API.
-   Respuestas.
-   Modelos internos.

------------------------------------------------------------------------

# 5. Definición de herramientas para modelado UML

Analizar herramientas compatibles con Python 3.12.

## PyEcore

Evaluar como representación interna del metamodelo UML.

Debe permitir representar:

-   Clase.
-   Atributo.
-   Método.
-   Relación.
-   Herencia.
-   Interfaces.

Definir cómo será utilizado para almacenar modelos UML independientes de
la representación gráfica.

------------------------------------------------------------------------

## Graphviz

Uso:

-   Renderizado de diagramas.
-   Exportación visual.
-   Generación de imágenes UML.

------------------------------------------------------------------------

## OpenCV

Uso:

Procesamiento de imágenes.

Aplicación futura:

-   Detección de diagramas UML.
-   Preparación de imágenes para IA.

------------------------------------------------------------------------

## Tesseract OCR

Uso:

Extracción de texto desde imágenes.

Aplicación:

Reconocer:

-   Nombre de clases.
-   Atributos.
-   Métodos.

------------------------------------------------------------------------

# 6. Definición del componente de Inteligencia Artificial

Establecer arquitectura inicial de IA.

La plataforma debe considerar:

-   IA para texto a UML.
-   IA para voz a UML.
-   IA para imagen a UML.
-   IA para validación.
-   IA para generación código.

------------------------------------------------------------------------

# Modelos locales

Evaluar:

-   Llama.
-   Mistral.
-   Qwen.

Herramientas:

-   Ollama.
-   llama.cpp.

Objetivo:

Permitir ejecución sin conexión a internet.

------------------------------------------------------------------------

# Entrenamiento y ajuste

Definir herramientas:

## PyTorch

Uso:

-   Entrenamiento.
-   Fine tuning.
-   Desarrollo de modelos propios.

## Transformers

Uso:

-   Adaptación de modelos.
-   Procesamiento de lenguaje natural.

------------------------------------------------------------------------

# 7. Definición del enfoque colaborativo

Diseñar la estrategia de colaboración.

Analizar:

-   Manejo de usuarios simultáneos.
-   Sincronización.
-   Resolución de conflictos.
-   Historial de cambios.

Evaluar:

-   Control optimista.
-   Event sourcing parcial.
-   Versionamiento de modelos.

Definir cómo cada modificación del UML será registrada como evento.

Ejemplo:

Evento:

CREATE_CLASS

Datos:

-   Usuario.
-   Fecha.
-   Proyecto.
-   Clase creada.

------------------------------------------------------------------------

# 8. Definición de estructura inicial del proyecto

Crear estructura base:

Frontend:

    frontend/
     ├── src/
     ├── components/
     ├── pages/
     ├── services/
     ├── stores/
     └── uml-editor/

Backend:

    backend/
     ├── app/
     │   ├── api/
     │   ├── models/
     │   ├── services/
     │   ├── websocket/
     │   └── database/

IA:

    ai-engine/
     ├── models/
     ├── training/
     ├── inference/
     └── datasets/

------------------------------------------------------------------------

# 9. Entregables de la fase

La fase debe generar:

-   Documento de arquitectura tecnológica.
-   Justificación de tecnologías.
-   Diagrama de arquitectura general.
-   Diagrama de componentes.
-   Estructura inicial del proyecto.
-   Configuración inicial del entorno.
-   Documento de librerías seleccionadas.
-   Documento de estrategia colaborativa.
-   Documento inicial de arquitectura IA.

------------------------------------------------------------------------

# Casos de uso relacionados inicialmente

Durante esta fase se preparará la base para:

-   CU-01 Registrar cuenta de usuario.
-   CU-02 Gestionar autenticación.
-   CU-03 Gestionar perfil propio.
-   CU-04 Gestionar usuarios y roles globales.
-   CU-08 Gestionar proyectos de desarrollo.
-   CU-09 Gestionar integrantes y permisos del proyecto.
-   CU-10 Gestionar versiones y cambios del proyecto.

------------------------------------------------------------------------

# Restricciones importantes

No utilizar servicios externos de inteligencia artificial como
dependencia final del sistema.

Las APIs externas únicamente podrán utilizarse durante investigación,
pruebas o entrenamiento.

La solución final debe permitir ejecución offline mediante modelos
locales.

La generación automática debe producir:

-   Backend objetivo: Spring Boot.
-   Frontend móvil objetivo: Flutter.

La plataforma web principal debe mantenerse en:

-   React como frontend.
-   Python FastAPI como backend.
