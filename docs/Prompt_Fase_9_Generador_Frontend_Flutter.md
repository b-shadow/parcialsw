# PROMPT FASE 9: DESARROLLO DEL GENERADOR AUTOMÁTICO DE FRONTEND MÓVIL FLUTTER DESDE MODELOS UML

## Contexto general de la fase

Esta fase corresponde al desarrollo del motor encargado de transformar
automáticamente los modelos UML y la estructura generada del backend
Spring Boot en una aplicación móvil funcional desarrollada con Flutter.

Este componente representa una de las capacidades principales de la
plataforma CASE inteligente:

Modelo UML

↓

Análisis del dominio

↓

Interpretación de entidades y operaciones

↓

Generación automática

↓

Aplicación móvil Flutter funcional

El objetivo es que un usuario pueda diseñar un modelo UML y obtener una
aplicación móvil base con pantallas, formularios, navegación y consumo
de servicios generados automáticamente.

La generación debe producir código organizado, mantenible y basado en
buenas prácticas de desarrollo Flutter.

------------------------------------------------------------------------

# Objetivo general de la fase

Implementar un generador automático capaz de crear aplicaciones móviles
Flutter a partir de modelos UML y contratos del backend generado.

El generador debe producir:

-   Proyecto Flutter.
-   Arquitectura modular.
-   Modelos de datos.
-   Servicios API.
-   Pantallas.
-   Formularios.
-   Navegación.
-   Gestión de estado.
-   Validaciones.
-   Configuración inicial.
-   Documentación básica.

------------------------------------------------------------------------

# 1. Arquitectura del generador Flutter

El generador debe funcionar como un módulo independiente integrado con:

-   Motor UML.
-   Generador Spring Boot.
-   Backend FastAPI.
-   Motor IA local.

Arquitectura propuesta:

    flutter_generator/

    ├── uml_analyzer/

    ├── api_analyzer/

    ├── templates/

    ├── generator/

    ├── components/

    ├── validators/

    └── exporter/

------------------------------------------------------------------------

# 2. Responsabilidades de los componentes

## UML Analyzer

Responsable de interpretar:

-   Clases.
-   Atributos.
-   Relaciones.
-   Métodos.
-   Entidades principales.

------------------------------------------------------------------------

## API Analyzer

Analizar el backend generado:

-   Endpoints REST.
-   Métodos HTTP.
-   Parámetros.
-   Respuestas.
-   Modelos.

------------------------------------------------------------------------

## Templates

Contener plantillas reutilizables:

-   Pantallas.
-   Modelos.
-   Servicios.
-   Widgets.
-   Controladores.

------------------------------------------------------------------------

## Generator

Responsable de:

-   Crear archivos.
-   Crear carpetas.
-   Aplicar nombres.
-   Integrar componentes.

------------------------------------------------------------------------

# 3. Entrada del generador

El generador debe recibir:

## Modelo UML

Información:

-   Entidades.
-   Atributos.
-   Relaciones.
-   Operaciones.

------------------------------------------------------------------------

## Backend generado

Información:

-   Endpoints.
-   DTO.
-   Servicios disponibles.
-   Seguridad.

------------------------------------------------------------------------

# 4. Arquitectura Flutter generada

El código generado debe seguir una arquitectura modular.

Estructura propuesta:

    lib/

    ├── core/

    │   ├── network/

    │   ├── constants/

    │   ├── routes/

    │   └── utils/

    │

    ├── modules/

    │

    │   ├── autenticacion/

    │   ├── usuarios/

    │   ├── proyectos/

    │   ├── uml/

    │   └── generacion/

    │

    ├── shared/

    │   ├── widgets/

    │   └── themes/

    └── main.dart

------------------------------------------------------------------------

# 5. Tecnologías Flutter

Utilizar:

## Framework

Flutter.

## Lenguaje

Dart.

------------------------------------------------------------------------

# 6. Gestión de estado

Evaluar e implementar una solución adecuada.

Analizar:

-   Riverpod.
-   Bloc.
-   Provider.
-   GetX.

Seleccionar considerando:

-   Escalabilidad.
-   Código generado.
-   Mantenimiento.

------------------------------------------------------------------------

# 7. Generación de modelos Dart

Por cada entidad UML generar:

Ejemplo:

Usuario UML

↓

Usuario.dart

Debe incluir:

-   Propiedades.
-   Constructor.
-   Métodos fromJson.
-   Métodos toJson.
-   Conversión de datos.

------------------------------------------------------------------------

# 8. Generación de servicios API

Crear servicios para consumir Spring Boot.

Generar:

-   Cliente HTTP.
-   Métodos GET.
-   Métodos POST.
-   Métodos PUT.
-   Métodos DELETE.

Ejemplo:

UsuarioService

Debe manejar:

-   Solicitudes.
-   Respuestas.
-   Errores.
-   Estados de carga.

------------------------------------------------------------------------

# 9. Generación automática de pantallas

El sistema debe generar interfaces según las entidades UML.

Para cada entidad CRUD generar:

## Listado

Permitir:

-   Consultar registros.
-   Buscar.
-   Filtrar.

------------------------------------------------------------------------

## Registro

Generar:

-   Formularios.
-   Campos dinámicos.
-   Validaciones.

------------------------------------------------------------------------

## Edición

Permitir:

-   Modificar información.
-   Guardar cambios.

------------------------------------------------------------------------

## Detalle

Mostrar:

-   Información completa.
-   Relaciones.

------------------------------------------------------------------------

# 10. Generación de formularios dinámicos

Interpretar atributos UML.

Ejemplo:

nombre:String

↓

TextField

fecha:Date

↓

DatePicker

boolean

↓

Switch

Debe generar:

-   Campos.
-   Etiquetas.
-   Validaciones.
-   Mensajes error.

------------------------------------------------------------------------

# 11. Generación de navegación

Crear automáticamente:

-   Rutas.
-   Menús.
-   Navegación entre pantallas.

Evaluar:

-   GoRouter.
-   Navigator 2.0.

------------------------------------------------------------------------

# 12. Generación de componentes reutilizables

Crear widgets comunes:

-   Botones.
-   Inputs.
-   Cards.
-   Tablas.
-   Listas.
-   Modales.

------------------------------------------------------------------------

# 13. Diseño visual generado

Definir:

-   Tema.
-   Colores.
-   Tipografía.
-   Espaciados.

Aplicar:

-   Material Design.
-   Componentes reutilizables.

------------------------------------------------------------------------

# 14. Integración con autenticación

Generar:

-   Login.
-   Registro.
-   Recuperación contraseña.

Implementar:

-   Gestión token JWT.
-   Sesión.
-   Protección rutas.

------------------------------------------------------------------------

# 15. Integración con roles

Adaptar interfaz según:

## Administrador

Acceso:

-   Usuarios.
-   Configuración.

------------------------------------------------------------------------

## Editor

Acceso:

-   Proyectos.
-   Modelos.

------------------------------------------------------------------------

## Organizador

Acceso:

-   Administración proyecto.
-   Integrantes.
-   Permisos.

------------------------------------------------------------------------

# 16. Generación desde modelo UML complejo

Debe soportar:

## Relaciones

Ejemplo:

Usuario tiene muchos pedidos.

Generar:

-   Navegación relacionada.
-   Componentes adecuados.

------------------------------------------------------------------------

## Herencia

Generar:

-   Clases base.
-   Clases hijas.

------------------------------------------------------------------------

# 17. Integración con IA local

La IA puede participar en:

-   Mejorar diseño UI.
-   Sugerir pantallas.
-   Proponer componentes.
-   Optimizar estructura.

La generación base debe mantenerse determinista.

------------------------------------------------------------------------

# 18. Validación del código generado

Antes de entregar:

Validar:

-   Estructura Flutter.
-   Dependencias.
-   Compilación.
-   Errores Dart.

Ejecutar:

-   flutter analyze.
-   flutter build.

------------------------------------------------------------------------

# 19. Exportación del proyecto generado

Permitir:

-   Descargar proyecto ZIP.
-   Guardarlo dentro del proyecto.
-   Crear versión.

Registrar:

-   Usuario.
-   Fecha.
-   Modelo UML.
-   Versión generada.

------------------------------------------------------------------------

# 20. Versionamiento de generaciones

Guardar:

-   Modelo utilizado.
-   Código generado.
-   Configuración.
-   Historial.

Permitir:

-   Comparar generaciones.
-   Recuperar versiones anteriores.

------------------------------------------------------------------------

# 21. Pruebas del generador

Realizar:

## Pruebas simples

-   Una entidad.
-   CRUD básico.

## Pruebas intermedias

-   Varias entidades.
-   Relaciones.

## Pruebas avanzadas

-   Autenticación.
-   Roles.
-   Múltiples módulos.

------------------------------------------------------------------------

# 22. Documentación técnica

Generar:

-   Arquitectura del generador.
-   Reglas UML → Flutter.
-   Plantillas utilizadas.
-   Estructura código.
-   Manual ejecución.

------------------------------------------------------------------------

# Entregables de la fase

-   Motor generador Flutter.
-   Parser UML.
-   Analizador API.
-   Plantillas Flutter.
-   Generación modelos.
-   Generación pantallas.
-   Generación servicios.
-   Navegación.
-   Validaciones.
-   Exportación proyecto.
-   Documentación técnica.

------------------------------------------------------------------------

# Casos de uso relacionados

-   CU-16 Generar frontend móvil Flutter.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
