# PROMPT FASE 5: DESARROLLO DEL FRONTEND WEB REACT + TAILWIND CON ARQUITECTURA MODULAR POR PAQUETES FUNCIONALES

## Contexto general de la fase

Esta fase corresponde al desarrollo del frontend web principal de la
plataforma CASE inteligente y colaborativa.

El frontend será desarrollado utilizando:

-   React.
-   TypeScript.
-   Tailwind CSS.
-   Vite como herramienta de construcción.
-   Cliente HTTP para comunicación con APIs REST.
-   WebSockets para colaboración en tiempo real.

La aplicación web permitirá:

-   Gestionar usuarios y accesos.
-   Administrar proyectos colaborativos.
-   Crear y editar diagramas de clases UML.
-   Generar modelos mediante IA.
-   Importar y exportar modelos UML.
-   Ejecutar procesos de transformación y generación automática de
    software.

El frontend debe seguir una arquitectura estrictamente modular basada en
los cuatro paquetes funcionales definidos en el análisis del sistema.

No se debe organizar solamente por componentes técnicos, sino por
dominios funcionales.

------------------------------------------------------------------------

# Objetivo general de la fase

Desarrollar el frontend web utilizando React + Tailwind CSS con una
arquitectura modular basada en:

1.  Gestión de acceso, usuarios y seguimiento.
2.  Gestión de proyectos y colaboración.
3.  Modelado UML inteligente.
4.  Transformación y generación automática de software.

El frontend debe garantizar:

-   Interfaz moderna y responsive.
-   Separación clara de módulos.
-   Reutilización de componentes.
-   Comunicación con FastAPI.
-   Sincronización colaborativa mediante WebSockets.
-   Gestión de permisos según roles.

------------------------------------------------------------------------

# 1. Arquitectura modular del frontend

La estructura debe seguir los paquetes funcionales.

    frontend/

    src/

    ├── core/

    │   ├── api/

    │   ├── routes/

    │   ├── websocket/

    │   ├── config/

    │   └── auth/

    │

    ├── modules/

    │

    │   ├── gestion_acceso_usuarios/

    │   │

    │   ├── gestion_proyectos_colaboracion/

    │   │

    │   ├── modelado_uml_inteligente/

    │   │

    │   └── transformacion_generacion_software/

    │

    ├── shared/

    │   ├── components/

    │   ├── hooks/

    │   ├── icons/

    │   ├── layouts/

    │   └── utils/

    └── main.tsx

Cada módulo debe contener:

-   Pages.
-   Components.
-   Hooks.
-   Services.
-   Types.
-   Validations.
-   Estados propios.

------------------------------------------------------------------------

# 2. Tecnologías y librerías frontend

## Framework principal

-   React.

## Lenguaje

-   TypeScript.

## Herramienta construcción

-   Vite.

------------------------------------------------------------------------

# Estilos e interfaz

## Tailwind CSS

Será la librería principal de estilos.

Debe utilizarse para:

-   Layouts.
-   Responsive design.
-   Componentes.
-   Estados visuales.
-   Temas.

Evitar estilos CSS aislados salvo casos necesarios.

------------------------------------------------------------------------

# Componentes UI

Evaluar una librería compatible con Tailwind.

Recomendada:

## shadcn/ui

Utilizar para:

-   Botones.
-   Modales.
-   Formularios.
-   Dropdowns.
-   Tabs.
-   Cards.
-   Alertas.
-   Menús.

Ventaja:

Permite mantener control sobre los componentes y adaptarlos al diseño
del sistema.

------------------------------------------------------------------------

# Librerías de iconos

Utilizar:

## Lucide React

Para:

-   Menús.
-   Botones.
-   Acciones UML.
-   Estados.
-   Navegación.

Ejemplos:

-   Crear.
-   Editar.
-   Eliminar.
-   Exportar.
-   Configuración.

------------------------------------------------------------------------

Alternativas evaluadas:

-   React Icons.
-   Heroicons.

Seleccionar Lucide React como librería principal.

------------------------------------------------------------------------

# Gestión de estado

Evaluar e implementar:

## Zustand

Recomendado para:

-   Estado global ligero.
-   Usuario autenticado.
-   Proyecto activo.
-   Estado colaboración.

Complementar con:

React Context cuando corresponda.

------------------------------------------------------------------------

# Comunicación con backend

## Cliente HTTP

Utilizar:

-   Axios.

Implementar:

-   Interceptores.
-   Manejo JWT.
-   Manejo errores.
-   Estados de carga.

------------------------------------------------------------------------

# Comunicación tiempo real

Utilizar:

-   WebSocket.

Responsable de:

-   Cambios UML.
-   Usuarios conectados.
-   Eventos colaborativos.

------------------------------------------------------------------------

# 3. Módulo 1: Gestión de acceso, usuarios y seguimiento

Casos de uso relacionados:

-   CU-01 Gestionar cuenta de usuario.
-   CU-02 Gestionar usuarios y roles globales.
-   CU-03 Consultar reportes del proyecto.
-   CU-04 Consultar bitácora del proyecto.
-   CU-05 Consultar manual de usuario guiado.

Implementar:

## Autenticación

Pantallas:

-   Inicio de sesión.
-   Registro.
-   Recuperación de contraseña.

------------------------------------------------------------------------

## Perfil

Permitir:

-   Visualizar datos.
-   Editar información.
-   Configuración personal.

------------------------------------------------------------------------

## Administración

Para Administrador:

-   Usuarios.
-   Roles.
-   Estados.

------------------------------------------------------------------------

## Reportes

Crear:

-   Dashboard.
-   Indicadores.
-   Gráficos.

------------------------------------------------------------------------

## Manual guiado

Implementar asistente visual:

-   Recorridos del sistema.
-   Explicación de funcionalidades.
-   Ayuda contextual.

------------------------------------------------------------------------

# 4. Módulo 2: Gestión de proyectos y colaboración

Casos de uso relacionados:

-   CU-06 Gestionar proyectos de desarrollo.
-   CU-07 Gestionar integrantes y permisos del proyecto.
-   CU-08 Gestionar versiones y cambios del proyecto.
-   CU-09 Sincronizar proyectos con plataforma cloud.

Implementar:

## Gestión proyectos

Interfaces:

-   Listado.
-   Crear.
-   Editar.
-   Eliminar.
-   Acceso al entorno.

------------------------------------------------------------------------

## Integrantes

Permitir:

-   Invitar usuarios.
-   Gestionar permisos.
-   Visualizar participantes.

Roles:

-   Organizador.
-   Editor.

------------------------------------------------------------------------

## Versionamiento

Interfaces:

-   Historial.
-   Comparación.
-   Restauración.

------------------------------------------------------------------------

# 5. Módulo 3: Modelado UML inteligente

Casos de uso relacionados:

-   CU-10 Crear y editar diagramas de clases UML.
-   CU-11 Generar diagramas de clases UML mediante procesamiento de
    imágenes.
-   CU-12 Importar y exportar modelos UML.
-   CU-13 Validar diagramas de clases UML.

Este será el módulo principal del frontend.

------------------------------------------------------------------------

# Editor UML

Implementar:

-   Área de trabajo.
-   Barra de herramientas.
-   Panel de propiedades.
-   Panel de elementos.
-   Menú contextual.

Permitir:

-   Crear clases.
-   Editar clases.
-   Eliminar clases.
-   Crear atributos.
-   Crear métodos.
-   Crear relaciones.
-   Definir herencia.
-   Mover elementos.

------------------------------------------------------------------------

# Librerías para diagramación UML

Evaluar:

## React Flow

Principal candidata.

Usar para:

-   Nodos.
-   Relaciones.
-   Canvas.
-   Interacción gráfica.

Evaluar también:

-   JointJS.
-   GoJS.
-   D3.js.

Seleccionar según:

-   Personalización UML.
-   Rendimiento.
-   Licenciamiento.
-   Colaboración.

------------------------------------------------------------------------

# Colaboración UML

Implementar WebSocket:

Eventos:

-   Crear clase.
-   Modificar clase.
-   Eliminar clase.
-   Crear relación.
-   Mover elemento.

Actualizar:

-   Canvas.
-   Usuarios conectados.
-   Estado del modelo.

------------------------------------------------------------------------

# Imagen a UML

Interfaz:

-   Subir imagen.
-   Vista previa.
-   Enviar procesamiento.
-   Mostrar resultado.

------------------------------------------------------------------------

# XMI

Interfaces:

-   Importar modelo.
-   Exportar modelo.
-   Compatibilidad Enterprise Architect.

------------------------------------------------------------------------

# 6. Módulo 4: Transformación y generación automática de software

Casos de uso relacionados:

-   CU-14 Transformar modelo UML a estructura de implementación.
-   CU-15 Generar backend Spring Boot.
-   CU-16 Generar frontend móvil Flutter.
-   CU-17 Ejecutar generación mediante IA local offline.

Implementar interfaces:

## Transformación UML

Mostrar:

-   Modelo seleccionado.
-   Proceso.
-   Resultado.

------------------------------------------------------------------------

## Generación Spring Boot

Permitir:

-   Configuración.
-   Ejecución.
-   Progreso.
-   Resultado.

------------------------------------------------------------------------

## Generación Flutter

Permitir:

-   Selección modelo.
-   Generación.
-   Visualización resultado.

------------------------------------------------------------------------

## IA local offline

Interfaz:

-   Texto.
-   Voz.
-   Imagen.
-   Resultado generado.

------------------------------------------------------------------------

# 7. Diseño visual general

Definir:

-   Sistema de diseño.
-   Colores.
-   Tipografía.
-   Espaciados.
-   Componentes reutilizables.

Utilizar:

-   Tailwind CSS.
-   shadcn/ui.
-   Lucide React.

------------------------------------------------------------------------

# 8. Navegación y permisos

Implementar:

-   Rutas protegidas.
-   Layout principal.
-   Menú dinámico.

Según:

Administrador.

Editor.

Organizador.

------------------------------------------------------------------------

# 9. Pruebas frontend

Realizar:

## Unitarias

-   Componentes.
-   Hooks.
-   Servicios.

## Integración

-   APIs.
-   WebSockets.

## Usuario

-   Flujos principales.

------------------------------------------------------------------------

# 10. Documentación técnica

Generar:

-   Arquitectura frontend.
-   Estructura modular.
-   Librerías utilizadas.
-   Guía instalación.
-   Guía ejecución.

------------------------------------------------------------------------

# Entregables de la fase

-   Frontend React funcional.
-   Tailwind CSS implementado.
-   Arquitectura modular por paquetes.
-   Componentes reutilizables.
-   Integración FastAPI.
-   WebSockets.
-   Editor UML inicial.
-   Interfaces generación software.
-   Documentación técnica.

------------------------------------------------------------------------

# Detallar casos de uso

Pegar detallar casos de uso.
