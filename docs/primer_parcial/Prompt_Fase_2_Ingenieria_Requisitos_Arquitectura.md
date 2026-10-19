# PROMPT FASE 2: INGENIERÍA DE REQUISITOS Y DISEÑO ARQUITECTÓNICO DEL SISTEMA

## Contexto de la fase

Esta fase corresponde a la definición formal del sistema antes de
iniciar la implementación.

El proyecto consiste en una plataforma CASE inteligente y colaborativa
para creación, edición, análisis y transformación de diagramas de clases
UML hacia software funcional.

La plataforma permitirá:

-   Crear proyectos colaborativos.
-   Diseñar diagramas de clases UML.
-   Editar modelos mediante interfaz gráfica, texto y voz.
-   Procesar imágenes de diagramas UML.
-   Importar y exportar modelos mediante XMI.
-   Validar modelos UML.
-   Generar backend Spring Boot.
-   Generar frontend móvil Flutter.
-   Ejecutar procesos inteligentes mediante IA local offline.

La fase debe transformar la idea general del sistema en una
especificación técnica completa que sirva como base para las siguientes
etapas de desarrollo.

------------------------------------------------------------------------

# Objetivo general de la fase

Realizar el análisis completo del sistema mediante ingeniería de
requisitos y diseño arquitectónico, definiendo:

-   Alcance funcional.
-   Requerimientos funcionales.
-   Requerimientos no funcionales.
-   Actores.
-   Casos de uso.
-   Arquitectura lógica.
-   Arquitectura física.
-   Arquitectura de componentes.
-   Flujos principales del sistema.
-   Relaciones entre módulos.

------------------------------------------------------------------------

# 1. Análisis del problema y alcance del sistema

Desarrollar una descripción completa del problema que resuelve la
plataforma.

Debe explicarse:

-   Limitaciones actuales del desarrollo tradicional de software.
-   Necesidad de herramientas CASE inteligentes.
-   Problema de crear modelos UML y luego convertirlos manualmente en
    código.
-   Importancia de automatizar la generación de software.
-   Necesidad de colaboración en tiempo real.
-   Importancia del funcionamiento offline de la inteligencia
    artificial.

Definir claramente el alcance:

## Dentro del alcance

-   Gestión de usuarios.
-   Gestión de proyectos colaborativos.
-   Editor UML.
-   IA para creación de diagramas.
-   Importación/exportación UML.
-   Validación automática.
-   Generación backend Spring Boot.
-   Generación frontend Flutter.
-   IA local offline.

## Fuera del alcance inicial

Definir funcionalidades que no serán desarrolladas en esta versión.

------------------------------------------------------------------------

# 2. Identificación de actores del sistema

Documentar los actores principales.

## AC-01 Administrador

Responsable de la administración global de la plataforma.

Funciones:

-   Gestionar usuarios.
-   Gestionar roles globales.
-   Supervisar funcionamiento general.
-   Consultar información administrativa.

------------------------------------------------------------------------

## AC-02 Editor

Usuario que participa en proyectos colaborativos.

Funciones:

-   Crear proyectos.
-   Editar modelos UML.
-   Participar en diagramas.
-   Generar software.
-   Consultar información del proyecto.

------------------------------------------------------------------------

## AC-03 Organizador

Usuario responsable administrativo dentro de un proyecto específico.

Funciones:

-   Crear proyectos.
-   Administrar integrantes.
-   Gestionar permisos internos.
-   Controlar versiones.
-   Supervisar cambios.

------------------------------------------------------------------------

## Actores secundarios

Definir componentes externos:

### Inteligencia Artificial Local

Responsable de:

-   Interpretar instrucciones.
-   Analizar modelos.
-   Generar contenido.
-   Ejecutar procesos inteligentes offline.

### Enterprise Architect

Sistema externo relacionado con:

-   Importación XMI.
-   Exportación XMI.

------------------------------------------------------------------------

# 3. Definición de requerimientos funcionales

Crear la especificación detallada de funcionalidades del sistema.

Organizar por módulos.

------------------------------------------------------------------------

# Módulo 1: Gestión de acceso, usuarios y seguimiento

Definir requerimientos relacionados con:

-   Registro de usuarios.
-   Autenticación.
-   Gestión de perfiles.
-   Administración de roles.
-   Reportes.
-   Bitácora.
-   Manual guiado.

Casos de uso relacionados:

-   CU-01
-   CU-02
-   CU-03
-   CU-04
-   CU-05
-   CU-06
-   CU-07

------------------------------------------------------------------------

# Módulo 2: Gestión de proyectos y colaboración

Definir requerimientos para:

-   Creación de proyectos.
-   Espacios colaborativos.
-   Integrantes.
-   Permisos.
-   Versionamiento.
-   Historial de cambios.

Debe especificarse:

-   Cómo un Editor crea un proyecto.
-   Cómo pasa a ser Organizador.
-   Cómo otros usuarios ingresan como Editores.
-   Cómo se gestionan permisos internos.

Casos de uso relacionados:

-   CU-08
-   CU-09
-   CU-10

------------------------------------------------------------------------

# Módulo 3: Modelado UML inteligente

Definir requerimientos relacionados con:

-   Creación manual de diagramas.
-   Edición gráfica.
-   Creación mediante texto.
-   Creación mediante voz.
-   Procesamiento de imágenes.
-   Validación UML.
-   Importación/exportación.

Casos de uso relacionados:

-   CU-11
-   CU-12
-   CU-13
-   CU-14

------------------------------------------------------------------------

# Módulo 4: Transformación y generación automática

Definir requerimientos relacionados con:

-   Conversión UML a estructura de implementación.
-   Generación backend.
-   Generación frontend.
-   Ejecución IA local.

Casos de uso relacionados:

-   CU-15
-   CU-16
-   CU-17
-   CU-18

------------------------------------------------------------------------

# 4. Requerimientos no funcionales

Definir características de calidad del sistema.

## Rendimiento

Considerar:

-   Tiempo de respuesta del editor.
-   Sincronización colaborativa.
-   Procesamiento IA.
-   Generación código.

------------------------------------------------------------------------

## Seguridad

Definir:

-   Autenticación.
-   Control de acceso.
-   Protección de proyectos.
-   Manejo de permisos.

------------------------------------------------------------------------

## Disponibilidad

Considerar:

-   Funcionamiento plataforma web.
-   Persistencia de información.
-   Recuperación ante errores.

------------------------------------------------------------------------

## Escalabilidad

Definir:

-   Múltiples usuarios simultáneos.
-   Múltiples proyectos.
-   Crecimiento de modelos UML.

------------------------------------------------------------------------

## Compatibilidad

Definir compatibilidad con:

-   Navegadores web.
-   Sistemas operativos.
-   Herramientas UML externas.

------------------------------------------------------------------------

## Offline

Definir requisitos para:

-   Ejecución IA local.
-   Ausencia de conexión externa.
-   Procesamiento local de información.

------------------------------------------------------------------------

# 5. Diseño arquitectónico del sistema

Realizar el diseño general de arquitectura.

Debe incluir:

## Arquitectura de alto nivel

Representar:

Frontend React

↓

Backend FastAPI

↓

PostgreSQL

↓

Motor UML

↓

Motor IA

↓

Generadores Spring Boot / Flutter

------------------------------------------------------------------------

# 6. Diseño de arquitectura lógica

Definir módulos internos.

## Frontend React

Componentes:

-   Autenticación.
-   Gestión proyectos.
-   Editor UML.
-   Colaboración.
-   Panel IA.
-   Reportes.

------------------------------------------------------------------------

## Backend FastAPI

Componentes:

-   Usuarios.
-   Proyectos.
-   UML.
-   WebSocket.
-   Generación.
-   IA.
-   Auditoría.

------------------------------------------------------------------------

## Motor UML

Responsable de:

-   Modelo interno.
-   Clases.
-   Atributos.
-   Métodos.
-   Relaciones.

------------------------------------------------------------------------

## Motor IA

Responsable de:

-   Texto a UML.
-   Imagen a UML.
-   Voz a UML.
-   Validación.
-   Generación.

------------------------------------------------------------------------

# 7. Diseño de arquitectura colaborativa

Definir funcionamiento mediante WebSockets.

Debe documentarse:

-   Creación de sesiones colaborativas.
-   Conexión de usuarios.
-   Comunicación de eventos.
-   Actualización en tiempo real.

Ejemplo:

Usuario modifica clase.

↓

Frontend envía evento.

↓

Backend valida.

↓

Actualiza modelo.

↓

Distribuye cambio a usuarios conectados.

------------------------------------------------------------------------

# 8. Diseño de arquitectura física

Definir distribución de infraestructura.

Debe considerar:

## Cliente

-   Navegador web.
-   Aplicación móvil generada.

## Servidor aplicación

-   FastAPI.
-   WebSocket.
-   Servicios IA.

## Base datos

-   PostgreSQL.

## AWS

Definir posibles servicios:

-   EC2.
-   RDS.
-   S3.
-   CloudFront.

------------------------------------------------------------------------

# 9. Diagramas necesarios para la documentación

Generar:

-   Diagrama de arquitectura general.
-   Diagrama de componentes.
-   Diagrama de despliegue.
-   Diagrama de paquetes.
-   Diagrama de comunicación WebSocket.
-   Diagrama general de flujo del sistema.

------------------------------------------------------------------------

# 10. Matriz de trazabilidad

Crear relación entre:

-   Requerimientos.
-   Casos de uso.
-   Módulos.
-   Componentes.

Ejemplo:

Requerimiento:

"Permitir colaboración UML"

Relacionado con:

-   CU-11.
-   CU-10.
-   Módulo UML.
-   WebSocket.

------------------------------------------------------------------------

# 11. Entregables de la fase

La fase debe generar:

-   Documento de análisis del sistema.
-   Documento de requerimientos.
-   Documento de arquitectura.
-   Identificación de actores.
-   Requerimientos funcionales.
-   Requerimientos no funcionales.
-   Diagramas arquitectónicos.
-   Matriz de trazabilidad.

------------------------------------------------------------------------

# Casos de uso

CU01. Caso de Uso: Registrar cuenta de usuario

Nombre de Caso de Uso	Registrar cuenta de usuario
Propósito	Permitir que una persona cree una cuenta dentro de la plataforma para acceder a las funcionalidades disponibles como Editor.
Resumen	El usuario ingresa sus datos personales y credenciales de acceso. El sistema valida la información, crea la cuenta y asigna el rol inicial Editor para permitir su participación dentro de proyectos.
Actor(es)	Editor
Actor iniciador	Editor
Precondiciones	•	El correo electrónico utilizado no debe estar registrado previamente.
•	El usuario debe proporcionar los datos requeridos para crear la cuenta.
Flujo Principal	1)	El usuario selecciona la opción de registrarse dentro de la plataforma.
2)	El sistema muestra el formulario de creación de cuenta.
3)	El usuario ingresa sus datos personales y credenciales de acceso.
4)	El usuario confirma la solicitud de registro.
5)	El sistema valida la información ingresada.
6)	El sistema verifica que el correo electrónico no esté registrado.
7)	El sistema crea la cuenta del usuario.
8)	El sistema asigna el rol inicial Editor.
9)	El sistema confirma la creación de la cuenta.
Postcondiciones	•	La cuenta queda registrada dentro del sistema.
•	El usuario queda asociado al rol Editor.
•	El usuario puede utilizar sus credenciales para acceder a la plataforma.
Flujos Alternativos o Excepciones	E1. Información incompleta o inválida
•	Descripción: El usuario ingresa datos obligatorios incompletos o con formato incorrecto.
•	Acción del Sistema: El sistema muestra los mensajes de validación correspondientes y solicita corregir la información.
E2. Correo electrónico registrado
•	Descripción: El usuario intenta registrarse utilizando un correo asociado a una cuenta existente.
•	Acción del Sistema: El sistema informa que el correo ya está registrado y no permite crear la cuenta.

CU02. Caso de Uso: Gestionar autenticación

Nombre de Caso de Uso	Gestionar autenticación
Propósito	Permitir que los usuarios ingresen y salgan de la plataforma, además de recuperar el acceso a su cuenta cuando sea necesario.
Resumen	El usuario utiliza sus credenciales para ingresar al sistema. La plataforma valida la información, identifica los permisos asociados y permite acceder a las funcionalidades correspondientes. También permite cerrar sesión y recuperar la contraseña.
Actor(es)	Administrador, Editor, Organizador
Actor iniciador	Administrador, Editor, Organizador
Precondiciones	•	El usuario debe contar con una cuenta registrada.
•	Para recuperar contraseña, debe existir una cuenta asociada al correo ingresado.
•	Para cerrar sesión, el usuario debe tener una sesión activa.
Flujo Principal	Iniciar sesión
1)	El usuario accede a la pantalla de inicio de sesión.
2)	El sistema muestra los campos de acceso.
3)	El usuario ingresa correo electrónico y contraseña.
4)	El usuario selecciona la opción iniciar sesión.
5)	El sistema valida las credenciales ingresadas.
6)	El sistema permite el acceso a la plataforma.
Cerrar sesión
1)	El usuario selecciona la opción cerrar sesión desde la interfaz principal.
2)	El sistema solicita confirmación de cierre.
3)	El usuario confirma la acción.
4)	El sistema finaliza la sesión activa.
5)	El sistema retorna a la pantalla de acceso.
Recuperar contraseña
1)	El usuario selecciona la opción de recuperación de contraseña.
2)	El sistema solicita el correo asociado a la cuenta.
3)	El usuario ingresa su correo electrónico.
4)	El sistema valida la existencia de la cuenta.
5)	El sistema permite establecer una nueva contraseña.
6)	El usuario confirma la actualización.
7)	El sistema actualiza la contraseña.
Postcondiciones	•	El usuario queda autenticado y puede acceder según sus permisos.
•	La sesión queda finalizada cuando el usuario realiza el cierre correspondiente.
•	La contraseña queda actualizada cuando se completa la recuperación de acceso.
Flujos Alternativos o Excepciones	E1. Credenciales incorrectas
•	Descripción: El usuario ingresa un correo o contraseña que no coincide con la información registrada.
•	Acción del Sistema: El sistema rechaza el acceso e informa que las credenciales no son válidas.
E2. Cuenta deshabilitada
•	Descripción: El usuario intenta ingresar con una cuenta que se encuentra inactiva.
•	Acción del Sistema: El sistema bloquea el acceso e informa el estado de la cuenta.
E3. Correo no registrado
•	Descripción: El usuario solicita recuperar contraseña utilizando un correo que no pertenece a una cuenta existente.
•	Acción del Sistema: El sistema informa que no existe una cuenta asociada al correo ingresado.

CU03. Caso de Uso: Gestionar perfil propio

Nombre de Caso de Uso	Gestionar perfil propio
Propósito	Permitir que los usuarios consulten y actualicen su información personal dentro de la plataforma.
Resumen	El usuario accede a su perfil para visualizar sus datos registrados, modificar la información permitida y guardar los cambios realizados. El sistema valida la información actualizada y mantiene los datos del usuario actualizados.
Actor(es)	Administrador, Editor, Organizador
Actor iniciador	Administrador, Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión correctamente.
•	El usuario debe acceder a la sección de perfil dentro de la plataforma.
Flujo Principal	1)	El usuario accede a la sección de perfil.
2)	El sistema muestra la información actual del usuario.
3)	El usuario selecciona la opción de editar información.
4)	El sistema habilita los campos permitidos para modificación.
5)	El usuario actualiza sus datos personales.
6)	El usuario confirma la actualización.
7)	El sistema valida la información ingresada.
8)	El sistema guarda los cambios realizados.
9)	El sistema muestra un mensaje confirmando la actualización del perfil.
Postcondiciones	•	La información del perfil queda actualizada.
•	Los nuevos datos quedan disponibles para futuras operaciones dentro del sistema.
•	El usuario mantiene sus permisos y rol asignado sin modificaciones.
Flujos Alternativos o Excepciones	E1. Información inválida
•	Descripción: El usuario ingresa información con formato incorrecto o datos no permitidos.
•	Acción del Sistema: El sistema muestra los errores encontrados y solicita corregir la información.
E2. Campos obligatorios incompletos
•	Descripción: El usuario intenta guardar cambios sin completar información requerida.
•	Acción del Sistema: El sistema solicita completar los campos necesarios antes de actualizar el perfil.

CU04. Caso de Uso: Gestionar usuarios y roles globales

Nombre de Caso de Uso	Gestionar usuarios y roles globales
Propósito	Permitir que el Administrador gestione las cuentas registradas en la plataforma y controle los roles globales asignados a cada usuario.
Resumen	El Administrador administra los usuarios del sistema mediante el registro, modificación, activación, desactivación y asignación de roles globales. Estas acciones determinan los permisos generales de acceso dentro de la plataforma.
Actor(es)	Administrador
Actor iniciador	Administrador
Precondiciones	•	El Administrador debe haber iniciado sesión correctamente.
•	Para modificar una cuenta, el usuario debe existir previamente.
Flujo Principal	1)	El Administrador accede al módulo de gestión de usuarios.
2)	El sistema muestra el listado de usuarios registrados.
3)	El Administrador selecciona la acción requerida.
Registrar usuario
4)	El Administrador selecciona la opción de crear usuario.
5)	El sistema muestra el formulario de registro.
6)	El Administrador ingresa la información del nuevo usuario.
7)	El sistema valida la información y registra la cuenta.
Modificar usuario
8)	El Administrador selecciona un usuario registrado.
9)	El sistema muestra la información actual.
10)	El Administrador modifica los datos permitidos.
11)	El sistema valida y guarda los cambios.
Gestionar roles y estado
12)	El Administrador selecciona un usuario existente.
13)	El Administrador modifica el rol global o cambia el estado de la cuenta.
14)	El sistema actualiza los permisos o estado asignado.
15)	El sistema confirma la operación realizada. |
Postcondiciones	•	Los usuarios quedan registrados o actualizados correctamente.
•	Los roles globales quedan asignados según la configuración establecida.
•	Las cuentas pueden quedar habilitadas o deshabilitadas según la acción realizada.
Flujos Alternativos o Excepciones	E1. Información inválida
•	Descripción: El Administrador ingresa datos incompletos o incorrectos al registrar o modificar un usuario.
•	Acción del Sistema: El sistema solicita corregir la información antes de guardar los cambios.
E2. Correo electrónico registrado
•	Descripción: El Administrador intenta crear un usuario con un correo asociado a otra cuenta.
•	Acción del Sistema: El sistema informa que el correo ya se encuentra registrado.

CU05. Caso de Uso: Consultar reportes del proyecto

Nombre de Caso de Uso	Consultar reportes del proyecto
Propósito	Permitir que los integrantes del proyecto puedan consultar información resumida sobre el avance, estructura y elementos generados dentro del proyecto.
Resumen	El usuario accede al módulo de reportes del proyecto para visualizar métricas relacionadas con los diagramas UML, componentes generados, versiones y estado general del desarrollo. También puede exportar la información obtenida.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El usuario debe contar con permisos para consultar información del proyecto.
Flujo Principal	1)	El usuario ingresa al módulo de reportes del proyecto.
2)	El sistema muestra las opciones de consulta disponibles.
3)	El usuario selecciona el reporte que desea consultar.
4)	El sistema procesa la información del proyecto.
5)	El sistema muestra métricas relacionadas con clases UML, componentes generados, versiones y actividad del proyecto.
6)	El usuario puede aplicar filtros de consulta.
7)	El usuario selecciona la opción de exportar reporte si lo requiere.
8)	El sistema genera el reporte solicitado.
Postcondiciones	•	El usuario obtiene información resumida del estado del proyecto.
•	El reporte queda disponible para consulta o exportación según la acción realizada.
Flujos Alternativos o Excepciones	E1. Proyecto sin información disponible
•	Descripción: El usuario consulta reportes de un proyecto que aún no contiene información suficiente para generar métricas.
•	Acción del Sistema: El sistema informa que no existen datos disponibles para generar el reporte.

CU06. Caso de Uso: Consultar bitácora del proyecto

Nombre de Caso de Uso	Consultar bitácora del proyecto
Propósito	Permitir que el Organizador pueda revisar las acciones realizadas dentro de un proyecto para mantener la trazabilidad de cambios y actividades ejecutadas.
Resumen	El Organizador accede a la bitácora del proyecto para consultar eventos relacionados con modificaciones UML, generación de código, cambios de versiones e importaciones o exportaciones realizadas por los integrantes.
Actor(es)	Organizador
Actor iniciador	Organizador
Precondiciones	•	El Organizador debe haber iniciado sesión.
•	El Organizador debe pertenecer al proyecto consultado.
•	El proyecto debe contar con eventos registrados.
Flujo Principal	1)	El Organizador ingresa a la bitácora del proyecto.
2)	El sistema muestra el historial de eventos registrados.
3)	El Organizador consulta las acciones realizadas dentro del proyecto.
4)	El Organizador puede aplicar filtros por usuario, fecha o tipo de acción.
5)	El sistema muestra el detalle del evento seleccionado.
6)	El Organizador revisa la información de trazabilidad del proyecto.
Postcondiciones	•	El Organizador obtiene el historial de acciones realizadas dentro del proyecto.
•	La trazabilidad de modificaciones y operaciones queda disponible para consulta.
Flujos Alternativos o Excepciones	E1. Sin eventos registrados
•	Descripción: El Organizador consulta la bitácora de un proyecto que no tiene actividades registradas.
•	Acción del Sistema: El sistema informa que no existen eventos disponibles.

CU07. Caso de Uso: Consultar manual de usuario guiado

Nombre de Caso de Uso	Consultar manual de usuario guiado
Propósito	Permitir que los usuarios puedan recibir orientación sobre el uso de la plataforma mediante un asistente guiado que explique las funcionalidades disponibles del sistema.
Resumen	El usuario accede al manual guiado desde la plataforma para consultar información sobre módulos, opciones y pasos necesarios para realizar diferentes acciones dentro del sistema. El asistente proporciona orientación sobre el funcionamiento de la herramienta.
Actor(es)	Administrador, Editor, Organizador
Actor iniciador	Administrador, Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión en la plataforma.
•	El usuario debe acceder a la opción de asistente inteligente.
Flujo Principal	1)	El usuario accede al asistente inteligente.
2)	El sistema muestra el asistente de ayuda.
3)	El usuario selecciona la funcionalidad sobre la cual desea obtener información.
4)	El sistema identifica la opción consultada.
5)	El sistema muestra la explicación correspondiente.
6)	El usuario consulta los pasos necesarios para utilizar la funcionalidad.
7)	El sistema proporciona la guía de uso solicitada.
Postcondiciones	•	El usuario obtiene orientación sobre el uso de la plataforma.
•	El usuario puede continuar utilizando las funcionalidades del sistema con mayor conocimiento de su funcionamiento.
Flujos Alternativos o Excepciones	E1. Funcionalidad no disponible en la guía
•	Descripción: El usuario consulta una opción que aún no cuenta con información dentro del manual.
•	Acción del Sistema: El sistema informa que la guía para esa funcionalidad no está disponible.

CU08. Caso de Uso: Gestionar proyectos de desarrollo

Nombre de Caso de Uso	Gestionar proyectos de desarrollo
Propósito	Permitir que los usuarios puedan crear y administrar espacios de trabajo donde se desarrollarán los modelos UML y procesos de generación de software.
Resumen	El usuario crea un proyecto dentro de la plataforma, registra su información general, consulta los proyectos disponibles y administra su acceso según los permisos asignados. El Organizador del proyecto podrá gestionar posteriormente la colaboración dentro del mismo.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El usuario debe contar con permisos para crear o gestionar proyectos.
•	Para modificar o eliminar un proyecto, este debe existir previamente.
Flujo Principal	1)	El usuario accede al módulo de proyectos.
2)	El sistema muestra los proyectos disponibles y las opciones de gestión.
3)	El usuario accede al listado de proyectos disponibles.
4)	El sistema muestra los proyectos asociados al usuario.
Crear proyecto
5)	El usuario selecciona la opción crear proyecto.
6)	El sistema muestra el formulario de registro.
7)	El usuario ingresa la información general del proyecto.
8)	El usuario confirma la creación.
9)	El sistema registra el proyecto y asigna al creador como Organizador.
Consultar proyecto
10)	El usuario selecciona un proyecto.
11)	El sistema permite acceder al entorno de trabajo.
Modificar proyecto
12)	El Organizador selecciona un proyecto existente.
13)	El sistema muestra la información del proyecto.
14)	El Organizador modifica los datos permitidos.
15)	El sistema actualiza la información registrada.
Eliminar proyecto
16)	El Organizador selecciona la opción eliminar proyecto.
17)	El sistema solicita confirmación.
18)	El Organizador confirma la acción.
19)	El sistema elimina o desactiva el proyecto según la configuración establecida.
Postcondiciones	•	El proyecto queda creado y disponible para trabajar.
•	El usuario creador queda asignado como Organizador del proyecto.
•	La información del proyecto queda actualizada según las acciones realizadas.
•	Los proyectos eliminados dejan de estar disponibles para uso activo.
Flujos Alternativos o Excepciones	E1. Información incompleta
•	Descripción: El usuario intenta crear o modificar un proyecto sin completar los datos requeridos.
•	Acción del Sistema: El sistema solicita completar la información faltante.
E2. Nombre de proyecto duplicado
•	Descripción: El usuario intenta crear un proyecto con un nombre ya existente dentro de su espacio de trabajo.
•	Acción del Sistema: El sistema informa que el nombre ya está siendo utilizado.

CU09. Caso de Uso: Gestionar integrantes y permisos del proyecto

Nombre de Caso de Uso	Gestionar integrantes y permisos del proyecto
Propósito	Permitir que el Organizador administre los integrantes de un proyecto, controlando su participación y permisos dentro del espacio de trabajo colaborativo.
Resumen	El Organizador puede invitar Editores al proyecto, retirar integrantes y modificar permisos internos. El sistema mantiene la configuración de participantes asociada a cada proyecto.
Actor(es)	Organizador
Actor iniciador	Organizador
Precondiciones	•	El Organizador debe haber iniciado sesión.
•	El Organizador debe pertenecer al proyecto que desea administrar.
Flujo Principal	1)	El Organizador ingresa a la sección de integrantes del proyecto.
2)	El sistema muestra los usuarios asociados al proyecto y las opciones disponibles.
Invitar integrante
3)	El Organizador selecciona la opción de invitar usuario.
4)	El sistema solicita la información del integrante.
5)	El Organizador selecciona el usuario que desea agregar.
6)	El sistema incorpora al usuario como Editor del proyecto.
7)	Modificar permisos
8)	El Organizador selecciona un integrante existente.
9)	El sistema muestra los permisos disponibles.
10)	El Organizador actualiza los permisos permitidos.
11)	El sistema guarda la configuración modificada.
Retirar integrante
12)	El Organizador selecciona un integrante del proyecto.
13)	El sistema solicita confirmación de retiro.
14)	El Organizador confirma la acción.
15)	El sistema elimina la asociación del integrante con el proyecto.
Postcondiciones	•	Los integrantes del proyecto quedan actualizados.
•	Los permisos internos quedan configurados según la decisión del Organizador.
Flujos Alternativos o Excepciones	E1. Usuario no disponible
•	Descripción: El Organizador intenta agregar un usuario que no existe dentro de la plataforma.
•	Acción del Sistema: El sistema informa que el usuario no puede ser agregado.
E2. Integrante ya registrado
•	Descripción: El Organizador intenta invitar a un usuario que ya pertenece al proyecto.
•	Acción del Sistema: El sistema informa que el usuario ya forma parte del proyecto.

CU10. Caso de Uso: Gestionar versiones y cambios del proyecto

Nombre de Caso de Uso	Gestionar versiones y cambios del proyecto
Propósito	Permitir que los integrantes del proyecto administren versiones del trabajo realizado para mantener el control de modificaciones dentro del desarrollo.
Resumen	El usuario puede crear versiones del proyecto, registrar cambios realizados y recuperar estados anteriores del modelo. El sistema mantiene el historial de modificaciones para facilitar la gestión del desarrollo.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El proyecto debe contener información o modificaciones para generar versiones.
Flujo Principal	1)	El usuario accede al módulo de versiones del proyecto.
2)	El sistema muestra el historial de versiones disponibles.
Crear versión
3)	El usuario selecciona la opción crear versión.
4)	El sistema solicita la descripción del cambio realizado.
5)	El usuario registra la información de la versión.
6)	El sistema genera una nueva versión del proyecto.
Consultar cambios
7)	El usuario selecciona una versión existente.
8)	El sistema muestra la información registrada de la versión.
9)	El usuario revisa los cambios realizados.
Recuperar versión
10)	El usuario selecciona una versión anterior.
11)	El sistema muestra la información de recuperación.
12)	El usuario confirma la restauración.
13)	El sistema recupera la versión seleccionada.
Postcondiciones	•	Las versiones del proyecto quedan registradas.
•	Los cambios realizados quedan asociados al historial del proyecto.
•	El proyecto puede recuperar una versión anterior cuando corresponda.
Flujos Alternativos o Excepciones	E1. Sin cambios disponibles
•	Descripción: El usuario intenta crear una versión cuando no existen modificaciones registradas.
•	Acción del Sistema: El sistema informa que no existen cambios para generar una nueva versión.

CU11. Caso de Uso: Crear y editar diagramas de clases UML

Nombre de Caso de Uso	Crear y editar diagramas de clases UML
Propósito	Permitir que los usuarios construyan y modifiquen modelos UML mediante la creación de clases, atributos, métodos y relaciones dentro de un proyecto.
Resumen	El usuario accede al editor UML para crear o modificar diagramas de clases. Puede trabajar mediante herramientas gráficas o mediante instrucciones escritas o por voz, permitiendo definir la estructura del modelo y mantenerlo actualizado dentro del proyecto.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El proyecto debe estar disponible para edición.
Flujo Principal	14)	El usuario accede al módulo de diagramas UML.
Edición manual mediante editor UML
15)	El sistema muestra el editor gráfico del diagrama.
16)	El usuario crea clases dentro del lienzo de modelado.
17)	El usuario define atributos y métodos de cada clase.
18)	El usuario crea relaciones entre clases.
19)	El usuario define herencia, interfaces u otras relaciones UML.
20)	El usuario modifica o elimina elementos existentes.
21)	El sistema actualiza el modelo UML del proyecto.
Edición mediante instrucciones
22)	El usuario activa la entrada por voz(opcional)
23)	El usuario ingresa una instrucción textual para crear o modificar elementos UML.
24)	El sistema analiza la instrucción ingresada.
25)	El sistema identifica la acción solicitada.
26)	El sistema crea o modifica clases, atributos, métodos o relaciones.
27)	El sistema muestra los cambios realizados en el diagrama.
28)	El usuario confirma los cambios.
29)	El sistema guarda la actualización del modelo.
Postcondiciones	•	El diagrama de clases UML queda creado o actualizado.
•	Las clases, atributos, métodos y relaciones quedan almacenados dentro del proyecto.
•	El modelo queda disponible para procesos posteriores.
Flujos Alternativos o Excepciones	E1. Elemento UML inválido
•	Descripción: El usuario intenta crear una estructura UML que no cumple las reglas definidas.
•	Acción del Sistema: El sistema informa la inconsistencia y solicita corregir el elemento.
E2. Instrucción textual no comprendida
•	Descripción: La instrucción ingresada no permite identificar la acción requerida.
•	Acción del Sistema: El sistema solicita una nueva instrucción.
E3. Comando de voz no reconocido
•	Descripción: El sistema no logra interpretar correctamente la solicitud de voz.
•	Acción del Sistema: El sistema solicita repetir la instrucción.

CU12. Caso de Uso: Generar diagramas de clases UML mediante procesamiento de imágenes

Nombre de Caso de Uso	Generar diagramas de clases UML mediante procesamiento de imágenes
Propósito	Permitir que el usuario transforme una imagen de un diagrama de clases UML en un modelo editable dentro de la plataforma mediante inteligencia artificial.
Resumen	El usuario proporciona una imagen de un diagrama UML existente. El sistema procesa la imagen, reconoce los elementos del modelo y genera una representación UML editable dentro del proyecto.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	Debe existir una imagen con un diagrama de clases UML para procesar.
Flujo Principal	1)	El usuario accede a la opción de generación mediante imagen.
2)	El sistema solicita seleccionar una imagen.
3)	El usuario carga la imagen del diagrama UML.
4)	El sistema valida el archivo recibido.
5)	Procesamiento mediante IA
6)	El sistema analiza la imagen cargada.
7)	El sistema identifica clases, atributos, métodos y relaciones.
8)	El sistema transforma la información reconocida en un modelo UML.
9)	El sistema genera el diagrama de clases editable.
10)	El sistema muestra el resultado generado.
11)	El usuario revisa el modelo obtenido.
12)	El usuario realiza correcciones si son necesarias.
13)	El usuario guarda el diagrama dentro del proyecto.
14)	El sistema almacena el modelo UML generado. |
Postcondiciones	•	El diagrama UML queda generado a partir de la imagen.
•	Los elementos reconocidos quedan disponibles para edición.
•	El modelo queda almacenado dentro del proyecto.
Flujos Alternativos o Excepciones	E1. Imagen no válida
•	Descripción: El usuario carga una imagen que no corresponde a un diagrama UML reconocible.
•	Acción del Sistema: El sistema informa que no puede procesar la imagen.
E2. Reconocimiento incompleto
•	Descripción: La inteligencia artificial no logra identificar todos los elementos del diagrama.
•	Acción del Sistema: El sistema genera un modelo parcial e indica los elementos pendientes de revisión.
E3. Imagen con baja calidad
•	Descripción: La imagen no permite identificar correctamente los componentes del diagrama.
•	Acción del Sistema: El sistema solicita una nueva imagen con mejor calidad.

CU13. Caso de Uso: Importar y exportar modelos UML

Nombre de Caso de Uso	Importar y exportar modelos UML
Propósito	Permitir el intercambio de modelos UML entre la plataforma y herramientas externas mediante formatos compatibles como XMI.
Resumen	El usuario puede importar diagramas de clases UML existentes desde herramientas externas o exportar los modelos creados dentro de la plataforma para utilizarlos en otras herramientas compatibles con UML.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	Para importar, debe existir un archivo UML compatible.
•	Para exportar, debe existir un modelo UML registrado dentro del proyecto.
Flujo Principal	1)	El usuario accede al módulo de gestión de modelos UML.
2)	El sistema muestra las opciones disponibles de importación y exportación.
Importar modelo UML
3)	El usuario selecciona la opción importar modelo.
4)	El sistema solicita seleccionar un archivo compatible.
5)	El usuario carga el archivo UML.
6)	El sistema analiza la estructura del modelo.
7)	El sistema convierte la información al formato interno de la plataforma.
8)	El sistema muestra el diagrama importado.
9)	El usuario revisa el modelo generado.
10)	El sistema almacena el modelo dentro del proyecto.
Exportar modelo UML
11)	El usuario selecciona un modelo UML del proyecto.
12)	El usuario selecciona la opción exportar modelo.
13)	El sistema genera el archivo en un formato compatible como XMI.
14)	El usuario obtiene el archivo generado para utilizarlo en herramientas externas.
Postcondiciones	•	El modelo UML queda importado y disponible dentro del proyecto.
•	El modelo UML puede ser exportado para su uso en herramientas compatibles.
•	La estructura del modelo mantiene compatibilidad con estándares UML.
Flujos Alternativos o Excepciones	E1. Archivo incompatible
•	Descripción: El usuario intenta importar un archivo que no corresponde a un formato soportado.
•	Acción del Sistema: El sistema rechaza el archivo e informa que el formato no es válido.
E2. Modelo UML inválido
•	Descripción: El archivo importado contiene elementos que no cumplen la estructura esperada.
•	Acción del Sistema: El sistema informa los elementos que no pueden ser interpretados correctamente.

CU14. Caso de Uso: Validar diagramas de clases UML

Nombre de Caso de Uso	Registrar cuenta de usuario
Propósito	Permitir que el usuario verifique la consistencia y calidad del modelo UML antes de utilizarlo para procesos de generación de software.
Resumen	El usuario solicita la validación de un diagrama de clases UML. El sistema analiza la estructura del modelo, identifica posibles inconsistencias y presenta observaciones para mejorar el diseño.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	Debe existir un diagrama de clases UML registrado.
Flujo Principal	1)	El usuario selecciona un diagrama de clases UML.
2)	El usuario solicita la validación del modelo.
3)	El sistema analiza la estructura del diagrama.
4)	El sistema revisa clases, atributos, métodos y relaciones existentes.
5)	El sistema identifica inconsistencias o posibles mejoras del modelo.
6)	El sistema muestra los resultados de la validación.
7)	El usuario revisa las observaciones generadas.
8)	El usuario puede realizar ajustes sobre el modelo UML.
Postcondiciones	•	El modelo UML queda evaluado mediante las reglas de validación definidas.
•	Las observaciones encontradas quedan disponibles para revisión del usuario.
Flujos Alternativos o Excepciones	E1. Diagrama sin elementos suficientes
•	Descripción: El usuario intenta validar un diagrama vacío o sin estructura mínima.
•	Acción del Sistema: El sistema informa que no existen elementos suficientes para realizar la validación.
E2. Validación sin observaciones
•	Descripción: El sistema no encuentra inconsistencias en el modelo analizado.
•	Acción del Sistema: El sistema informa que el diagrama cumple con las validaciones realizadas.

CU15. Caso de Uso: Transformar modelo UML a estructura de implementación

Nombre de Caso de Uso	Transformar modelo UML a estructura de implementación
Propósito	Permitir convertir un modelo de clases UML validado en una estructura preparada para la generación automática del software.
Resumen	El usuario selecciona un modelo UML del proyecto para iniciar el proceso de transformación. El sistema interpreta las clases, atributos, métodos y relaciones definidas, generando una estructura lógica que será utilizada para crear el backend y frontend correspondiente.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El modelo UML debe cumplir las validaciones necesarias para la transformación.
Flujo Principal	1)	El usuario selecciona un modelo UML del proyecto.
2)	El usuario solicita transformar el modelo a estructura de implementación.
3)	El sistema analiza las clases definidas en el diagrama.
4)	El sistema interpreta atributos, métodos y relaciones entre clases.
5)	El sistema identifica entidades, componentes y estructuras necesarias para la implementación.
6)	El sistema genera la estructura base de desarrollo.
7)	El sistema muestra la estructura generada al usuario.
8)	El usuario revisa la información obtenida.
9)	El sistema almacena la estructura de implementación asociada al proyecto.
Postcondiciones	•	El modelo UML queda convertido en una estructura preparada para generación de código.
•	La información necesaria para generar software queda disponible dentro del proyecto.
•	El modelo mantiene relación con la estructura generada.
Flujos Alternativos o Excepciones	E1. Modelo UML incompleto
•	Descripción: El usuario intenta transformar un modelo que no contiene información suficiente para generar una estructura.
•	Acción del Sistema: El sistema informa los elementos faltantes y no inicia la transformación.

CU16. Caso de Uso: Generar backend Spring Boot

Nombre de Caso de Uso	Generar backend Spring Boot
Propósito	Permitir la generación automática de un backend funcional basado en la estructura obtenida del modelo UML.
Resumen	El usuario solicita la generación del backend a partir del modelo transformado. El sistema genera la estructura del proyecto Spring Boot, incluyendo entidades, repositorios, servicios, controladores y configuraciones necesarias para la conexión con la base de datos.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	Debe existir una estructura de implementación generada a partir del modelo UML.
Flujo Principal	1)	El usuario selecciona la opción de generar backend.
2)	El sistema analiza la estructura de implementación del proyecto.
3)	El sistema genera la configuración inicial del proyecto Spring Boot.
4)	El sistema crea las entidades correspondientes a las clases UML.
5)	El sistema genera repositorios para la gestión de datos.
6)	El sistema genera servicios con la lógica necesaria.
7)	El sistema genera controladores REST para la comunicación externa.
8)	El sistema configura la conexión con PostgreSQL.
9)	El sistema genera la estructura completa del backend.
10)	El sistema muestra el resultado generado al usuario.
11)	El usuario revisa y obtiene el proyecto generado.
Postcondiciones	•	El proyecto backend Spring Boot queda generado.
•	Las entidades, servicios y controladores quedan creados según el modelo UML.
•	El backend queda preparado para ser utilizado por el frontend generado.
Flujos Alternativos o Excepciones	E1. Estructura UML no compatible
•	Descripción: La información transformada no contiene los elementos necesarios para generar el backend.
•	Acción del Sistema: El sistema informa los elementos faltantes y cancela la generación.

CU17. Caso de Uso: Generar frontend móvil Flutter

Nombre de Caso de Uso	Generar frontend móvil Flutter
Propósito	Permitir la generación automática de una aplicación móvil en Flutter basada en la estructura del backend y modelo UML generado previamente.
Resumen	El usuario solicita la generación del frontend móvil. El sistema interpreta las entidades, servicios y operaciones disponibles del backend para crear una aplicación Flutter con modelos, pantallas, formularios, navegación e integración con los servicios generados.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	Debe existir un backend Spring Boot generado previamente.
•	Debe existir una estructura de implementación asociada al proyecto.
Flujo Principal	1)	El usuario selecciona la opción de generar frontend móvil.
2)	El sistema analiza la estructura del backend disponible.
3)	El sistema identifica entidades, operaciones y servicios disponibles.
4)	El sistema genera los modelos de datos para Flutter.
5)	El sistema genera las pantallas necesarias para la interacción con el sistema.
6)	El sistema genera formularios según las operaciones disponibles.
7)	El sistema genera la navegación entre pantallas.
8)	El sistema crea los servicios de comunicación con el backend.
9)	El sistema integra la aplicación móvil con los servicios generados.
10)	El sistema genera la estructura del proyecto Flutter.
11)	El sistema muestra el resultado generado al usuario.
Postcondiciones	•	El proyecto móvil Flutter queda generado.
•	Las pantallas, modelos y servicios quedan creados según la estructura del sistema.
•	La aplicación móvil queda preparada para comunicarse con el backend generado.
Flujos Alternativos o Excepciones	E1. Backend no disponible
•	Descripción: El usuario intenta generar el frontend sin contar con un backend generado.
•	Acción del Sistema: El sistema informa que primero debe existir una estructura backend disponible.

CU18. Caso de Uso: Ejecutar generación mediante IA local offline

Nombre de Caso de Uso	Ejecutar generación mediante IA local offline
Propósito	Permitir que las funciones inteligentes de análisis, generación y modificación funcionen utilizando un modelo de inteligencia artificial ejecutado localmente sin conexión a internet.
Resumen	El usuario utiliza las capacidades de inteligencia artificial de la plataforma mediante un modelo instalado localmente. El sistema procesa instrucciones, analiza modelos UML y genera contenido sin depender de servicios externos en línea.
Actor(es)	Editor, Organizador
Actor iniciador	Editor, Organizador
Precondiciones	•	El usuario debe haber iniciado sesión.
•	El proyecto debe encontrarse disponible dentro del sistema.
Flujo Principal	1)	El usuario solicita una operación asistida mediante IA.
2)	El sistema carga el modelo de inteligencia artificial local.
3)	El sistema procesa la instrucción proporcionada por el usuario.
4)	El modelo local analiza la información recibida.
5)	El sistema genera la respuesta, modificación o componente solicitado.
6)	El sistema muestra el resultado generado.
7)	El usuario revisa y confirma la utilización del resultado.
8)	El sistema almacena los cambios dentro del proyecto.
Postcondiciones	•	La operación solicitada mediante IA queda ejecutada sin conexión externa.
•	Los resultados generados quedan disponibles dentro del proyecto.
Flujos Alternativos o Excepciones	E1. Solicitud no comprendida
•	Descripción: La IA local no logra interpretar correctamente la instrucción ingresada.
•	Acción del Sistema: El sistema solicita reformular la solicitud.

