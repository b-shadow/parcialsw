# PROMPT FASE 8: DESARROLLO DEL GENERADOR AUTOMÁTICO DE BACKEND SPRING BOOT DESDE MODELOS UML

## Contexto general de la fase

Esta fase corresponde al desarrollo del motor encargado de transformar
automáticamente un modelo UML generado dentro de la plataforma en un
backend funcional utilizando Spring Boot.

Este componente representa una de las capacidades principales del
sistema CASE inteligente:

Modelo UML de clases

↓

Análisis estructural

↓

Generación automática

↓

Proyecto backend Spring Boot funcional

El objetivo es que un usuario pueda crear un diagrama de clases UML y
obtener una aplicación backend inicial con una arquitectura profesional
basada en Spring Boot.

La generación debe producir código mantenible, modular y preparado para
ampliaciones posteriores.

------------------------------------------------------------------------

# Objetivo general de la fase

Implementar un generador automático capaz de interpretar modelos UML y
convertirlos en una estructura completa de backend utilizando:

-   Java.
-   Spring Boot.
-   Spring Data JPA.
-   Spring Web.
-   Spring Security.
-   PostgreSQL.

El generador debe crear:

-   Proyecto Spring Boot.
-   Configuración inicial.
-   Entidades.
-   Relaciones JPA.
-   DTO.
-   Repositorios.
-   Servicios.
-   Controladores REST.
-   Validaciones.
-   Manejo básico de excepciones.
-   Documentación API.

------------------------------------------------------------------------

# 1. Arquitectura del generador backend

El generador debe funcionar como un módulo independiente integrado al
sistema principal.

Arquitectura propuesta:

    backend_generator/

    ├── uml_parser/

    ├── analyzer/

    ├── templates/

    ├── generator/

    ├── validators/

    ├── exporter/

    └── services/

Responsabilidades:

## UML Parser

Responsable de:

-   Leer modelo UML.
-   Interpretar clases.
-   Interpretar atributos.
-   Interpretar métodos.
-   Interpretar relaciones.

------------------------------------------------------------------------

## Analyzer

Responsable de:

-   Analizar estructura.
-   Identificar entidades.
-   Detectar relaciones.
-   Determinar componentes necesarios.

------------------------------------------------------------------------

## Templates

Contener plantillas reutilizables:

-   Entidades.
-   Controladores.
-   Servicios.
-   Repositorios.
-   DTO.

------------------------------------------------------------------------

## Generator

Responsable de:

-   Crear archivos.
-   Crear paquetes.
-   Aplicar nombres.
-   Insertar código generado.

------------------------------------------------------------------------

# 2. Entrada del generador

El generador debe recibir como entrada el modelo UML interno.

Debe interpretar:

## Clases

Ejemplo:

Usuario

------------------------------------------------------------------------

## Atributos

Ejemplo:

-   id: Long
-   nombre: String
-   correo: String

------------------------------------------------------------------------

## Métodos

Ejemplo:

-   registrar()
-   actualizar()

------------------------------------------------------------------------

## Relaciones

Ejemplo:

Usuario 1:N Pedido

------------------------------------------------------------------------

# 3. Transformación UML hacia código

Definir reglas de conversión.

Ejemplo:

Clase UML:

Usuario

↓

Entidad Java:

Usuario.java

Atributo UML:

nombre:String

↓

Campo Java:

private String nombre;

Relación UML:

Uno a muchos

↓

Anotación JPA:

@OneToMany

------------------------------------------------------------------------

# 4. Generación de estructura del proyecto Spring Boot

El sistema debe crear automáticamente:

    proyecto-generado/

    src/main/java/

    ├── config/

    ├── controller/

    ├── dto/

    ├── entity/

    ├── repository/

    ├── service/

    └── exception/

Además:

    resources/

    ├── application.properties

    └── data.sql

------------------------------------------------------------------------

# 5. Generación de configuración inicial

Crear:

## pom.xml

Debe incluir dependencias:

-   Spring Web.
-   Spring Data JPA.
-   PostgreSQL Driver.
-   Lombok.
-   Validation.
-   Spring Security.

------------------------------------------------------------------------

## application.properties

Generar configuración:

-   Nombre aplicación.
-   Puerto.
-   Base de datos.
-   Hibernate.
-   JPA.

------------------------------------------------------------------------

# 6. Generación de entidades JPA

Por cada clase UML generar:

-   Clase Java.
-   Anotaciones JPA.
-   Identificador.
-   Campos.
-   Relaciones.

Ejemplo:

@Entity

@Table

@Id

@GeneratedValue

------------------------------------------------------------------------

Debe soportar:

-   OneToOne.
-   OneToMany.
-   ManyToOne.
-   ManyToMany.

------------------------------------------------------------------------

# 7. Generación de DTO

Crear objetos de transferencia.

Generar:

-   Request DTO.
-   Response DTO.

Objetivo:

-   Separar entidades internas.
-   Controlar información expuesta.

------------------------------------------------------------------------

# 8. Generación de repositorios

Por cada entidad crear:

Ejemplo:

UsuarioRepository

Utilizar:

JpaRepository.

Debe generar:

-   Métodos CRUD básicos.
-   Métodos derivados cuando corresponda.

------------------------------------------------------------------------

# 9. Generación de servicios

Crear capa de negocio.

Ejemplo:

UsuarioService

Debe contener:

-   Crear.
-   Consultar.
-   Actualizar.
-   Eliminar.

Aplicar:

-   Separación lógica.
-   Validaciones.
-   Manejo errores.

------------------------------------------------------------------------

# 10. Generación de controladores REST

Crear endpoints automáticamente.

Ejemplo:

UsuarioController

Generar:

POST

GET

PUT

DELETE

Ejemplo:

/api/usuarios

------------------------------------------------------------------------

Debe incluir:

-   Request mapping.
-   Validación entrada.
-   Respuestas HTTP correctas.

------------------------------------------------------------------------

# 11. Generación automática CRUD

El sistema debe identificar entidades CRUD.

Generar:

-   Crear registro.
-   Listar registros.
-   Buscar por ID.
-   Actualizar.
-   Eliminar.

------------------------------------------------------------------------

# 12. Generación de validaciones

Interpretar restricciones UML.

Ejemplo:

Campo obligatorio.

↓

@NotNull

Longitud máxima.

↓

@Size

Correo.

↓

@Email

------------------------------------------------------------------------

# 13. Manejo de excepciones

Generar:

-   Excepciones personalizadas.
-   GlobalExceptionHandler.
-   Respuestas estándar.

Ejemplo:

404

Entidad no encontrada.

400

Datos inválidos.

------------------------------------------------------------------------

# 14. Generación de seguridad inicial

Preparar estructura para:

-   Spring Security.
-   JWT.
-   Roles.

Debe considerar:

Roles definidos:

-   Administrador.
-   Editor.
-   Organizador.

------------------------------------------------------------------------

# 15. Arquitectura modular del backend generado

El código generado debe respetar separación modular.

Basarse en los paquetes funcionales:

## Gestión de acceso, usuarios y seguimiento

Incluye:

-   Usuarios.
-   Roles.
-   Autenticación.

------------------------------------------------------------------------

## Gestión de proyectos y colaboración

Incluye:

-   Proyectos.
-   Integrantes.
-   Versiones.

------------------------------------------------------------------------

## Modelado UML inteligente

Incluye:

-   Diagramas.
-   Clases UML.
-   Modelos.

------------------------------------------------------------------------

## Transformación y generación automática de software

Incluye:

-   Procesos generación.
-   Configuración.

------------------------------------------------------------------------

# 16. Integración con IA local

La IA puede participar en:

-   Optimización del código.
-   Sugerencia arquitectura.
-   Generación documentación.

Pero la generación base debe funcionar mediante reglas deterministas.

------------------------------------------------------------------------

# 17. Generación de documentación backend

Crear automáticamente:

## README

Incluyendo:

-   Descripción.
-   Instalación.
-   Ejecución.

------------------------------------------------------------------------

## Documentación API

Integrar:

-   Swagger/OpenAPI.

Generar:

-   Endpoints.
-   Parámetros.
-   Respuestas.

------------------------------------------------------------------------

# 18. Validación del código generado

Antes de entregar el proyecto:

Realizar:

## Validación estructural

Comprobar:

-   Archivos creados.
-   Paquetes correctos.

------------------------------------------------------------------------

## Validación compilación

Ejecutar:

-   Maven build.

Detectar:

-   Errores sintácticos.
-   Dependencias faltantes.

------------------------------------------------------------------------

# 19. Exportación del proyecto generado

Permitir:

-   Descargar proyecto ZIP.
-   Guardar dentro del proyecto CASE.
-   Crear versión generada.

Registrar:

-   Usuario.
-   Fecha.
-   Modelo UML utilizado.
-   Versión.

------------------------------------------------------------------------

# 20. Control de versiones de generación

Guardar:

-   Modelo UML origen.
-   Código generado.
-   Fecha.
-   Cambios.

Permitir comparar generaciones.

------------------------------------------------------------------------

# 21. Pruebas del generador

Realizar pruebas:

## Casos simples

-   Una entidad.
-   CRUD básico.

## Casos intermedios

-   Varias entidades.
-   Relaciones.

## Casos complejos

-   Herencia.
-   Relaciones múltiples.
-   Interfaces.

------------------------------------------------------------------------

# 22. Documentación técnica

Generar:

-   Arquitectura del generador.
-   Reglas UML → Java.
-   Plantillas.
-   Estructura código.
-   Flujo generación.

------------------------------------------------------------------------

# Entregables de la fase

-   Motor generador Spring Boot.
-   Parser UML.
-   Analizador de modelos.
-   Plantillas código.
-   Generación entidades.
-   Generación CRUD.
-   Generación REST API.
-   Validaciones.
-   Exportación proyecto.
-   Documentación técnica.

------------------------------------------------------------------------

# Casos de uso relacionados

-   CU-14 Transformar modelo UML a estructura de implementación.
-   CU-15 Generar backend Spring Boot.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
