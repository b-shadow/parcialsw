# Pruebas funcionales dirigidas por casos de uso

Estas pruebas validan el comportamiento observable del sistema CASE Inteligente a partir de los 18 casos de uso definidos en la Fase 2.

## Prueba de Caso de Uso CU-01: Registrar cuenta de usuario

> **Caso de uso:** CU-01 Registrar cuenta de usuario **ID de Prueba:** TS-CU01-01 **Descripcion:** Validar que un usuario nuevo pueda registrarse con datos validos y quedar disponible para autenticacion. **Precondiciones:** El correo ingresado no existe en el sistema.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir la pantalla de registro. | El sistema muestra el formulario de registro. | Satisfactorio |
| **2** | Ingresar nombre, correo y contrasena validos. | El sistema acepta los campos ingresados. | Satisfactorio |
| **3** | Enviar el formulario. | El backend valida datos, cifra la contrasena y crea la cuenta con rol Editor. | Satisfactorio |
| **4** | Intentar iniciar sesion con la cuenta creada. | El sistema permite autenticarse con las credenciales registradas. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-02: Gestionar autenticacion

> **Caso de uso:** CU-02 Gestionar autenticacion **ID de Prueba:** TS-CU02-01 **Descripcion:** Validar el inicio de sesion y habilitacion de rutas segun permisos. **Precondiciones:** Usuario activo registrado en el sistema.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir la pantalla de inicio de sesion. | El sistema muestra campos de correo y contrasena. | Satisfactorio |
| **2** | Ingresar credenciales validas. | El backend valida las credenciales. | Satisfactorio |
| **3** | Enviar inicio de sesion. | El sistema emite JWT y guarda la sesion en frontend. | Satisfactorio |
| **4** | Navegar al panel principal. | Las rutas disponibles corresponden al rol del usuario. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-03: Gestionar perfil propio

> **Caso de uso:** CU-03 Gestionar perfil propio **ID de Prueba:** TS-CU03-01 **Descripcion:** Validar consulta y actualizacion de datos del perfil del usuario autenticado. **Precondiciones:** Usuario autenticado con sesion activa.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir la opcion Perfil. | El sistema muestra nombre, correo y estado del usuario. | Satisfactorio |
| **2** | Modificar datos permitidos del perfil. | El formulario permite editar solo campos autorizados. | Satisfactorio |
| **3** | Guardar cambios. | El backend valida y persiste la informacion. | Satisfactorio |
| **4** | Cambiar contrasena desde el perfil. | El sistema valida la contrasena actual y actualiza la nueva. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-04: Gestionar usuarios y roles globales

> **Caso de uso:** CU-04 Gestionar usuarios y roles globales **ID de Prueba:** TS-CU04-01 **Descripcion:** Validar que el administrador gestione usuarios, estados y roles globales. **Precondiciones:** Usuario autenticado con rol Administrador.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir administracion de usuarios. | El sistema lista usuarios registrados. | Satisfactorio |
| **2** | Seleccionar un usuario. | El sistema muestra detalle de usuario, rol y estado. | Satisfactorio |
| **3** | Cambiar rol o estado global. | El backend valida permisos administrativos. | Satisfactorio |
| **4** | Guardar cambios. | El cambio se persiste y se registra en bitacora. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-05: Consultar reportes

> **Caso de uso:** CU-05 Consultar reportes **ID de Prueba:** TS-CU05-01 **Descripcion:** Validar la visualizacion de indicadores del proyecto. **Precondiciones:** Usuario autenticado con rol Administrador u Organizador y proyecto disponible.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir la pantalla Reportes. | El sistema muestra panel de reportes. | Satisfactorio |
| **2** | Seleccionar proyecto o filtros disponibles. | El sistema filtra informacion segun permisos. | Satisfactorio |
| **3** | Consultar indicadores. | Se muestran proyectos, actividad, cambios y generaciones. | Satisfactorio |
| **4** | Cambiar filtros. | Los indicadores se actualizan sin mostrar datos no autorizados. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-06: Consultar bitacora

> **Caso de uso:** CU-06 Consultar bitacora **ID de Prueba:** TS-CU06-01 **Descripcion:** Validar la consulta de acciones registradas por usuario, fecha y proyecto. **Precondiciones:** Usuario autenticado con permisos de Administrador u Organizador.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir la vista de bitacora. | El sistema muestra listado de eventos. | Satisfactorio |
| **2** | Aplicar filtro por proyecto. | El sistema retorna eventos del proyecto seleccionado. | Satisfactorio |
| **3** | Aplicar filtro por usuario o fecha. | El listado se actualiza con los criterios ingresados. | Satisfactorio |
| **4** | Revisar detalle de evento. | Se muestran accion, usuario, fecha y resultado. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-07: Consultar manual guiado

> **Caso de uso:** CU-07 Consultar manual guiado **ID de Prueba:** TS-CU07-01 **Descripcion:** Validar que el asistente contextual responda consultas sobre el uso del sistema. **Precondiciones:** Usuario autenticado dentro de cualquier modulo.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir el asistente flotante. | El sistema muestra una ventana de chat de ayuda. | Satisfactorio |
| **2** | Preguntar donde generar diagramas mediante imagen. | El asistente responde con pasos del modulo UML e imagen a UML. | Satisfactorio |
| **3** | Preguntar como generar backend. | El asistente indica seleccionar proyecto, diagrama, transformar UML y generar Spring Boot. | Satisfactorio |
| **4** | Cerrar y volver a abrir el asistente. | El asistente permanece disponible sin bloquear la navegacion. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-08: Gestionar proyectos de desarrollo

> **Caso de uso:** CU-08 Gestionar proyectos de desarrollo **ID de Prueba:** TS-CU08-01 **Descripcion:** Validar creacion, consulta y actualizacion basica de proyectos. **Precondiciones:** Usuario autenticado con rol Editor.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir Gestionar Proyectos. | El sistema muestra proyectos disponibles y formulario de creacion. | Satisfactorio |
| **2** | Crear proyecto con nombre y descripcion. | El backend valida datos y crea el proyecto. | Satisfactorio |
| **3** | Abrir el proyecto creado. | El usuario creador aparece como Organizador interno. | Satisfactorio |
| **4** | Editar datos generales del proyecto. | El sistema guarda cambios y actualiza la vista. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-09: Gestionar integrantes y permisos

> **Caso de uso:** CU-09 Gestionar integrantes y permisos **ID de Prueba:** TS-CU09-01 **Descripcion:** Validar adicion, modificacion y retiro de colaboradores del proyecto. **Precondiciones:** Usuario autenticado como Organizador del proyecto.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Abrir gestion de proyecto. | El sistema muestra seccion de colaboradores. | Satisfactorio |
| **2** | Seleccionar usuario y rol interno. | El sistema habilita la accion Agregar. | Satisfactorio |
| **3** | Agregar colaborador. | El backend valida permisos y registra al integrante. | Satisfactorio |
| **4** | Cambiar rol o retirar colaborador. | El sistema actualiza permisos y registra bitacora. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-10: Gestionar versiones y cambios

> **Caso de uso:** CU-10 Gestionar versiones y cambios **ID de Prueba:** TS-CU10-01 **Descripcion:** Validar guardado, consulta y restauracion de versiones del modelo. **Precondiciones:** Proyecto activo con un diagrama UML existente.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Guardar una version del modelo. | El sistema registra descripcion, usuario, fecha y estado del modelo. | Satisfactorio |
| **2** | Modificar el diagrama. | El sistema permite guardar una nueva version. | Satisfactorio |
| **3** | Abrir historial de versiones. | El sistema lista versiones disponibles. | Satisfactorio |
| **4** | Restaurar una version anterior. | El modelo vuelve al estado almacenado. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-11: Crear y editar diagramas de clases UML

> **Caso de uso:** CU-11 Crear y editar diagramas de clases UML **ID de Prueba:** TS-CU11-01 **Descripcion:** Validar creacion, edicion, relaciones y persistencia del diagrama UML. **Precondiciones:** Usuario Editor con proyecto activo seleccionado.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Crear un nuevo diagrama de clases. | El sistema abre el lienzo UML. | Satisfactorio |
| **2** | Agregar clases, atributos y metodos. | Los elementos se renderizan en el lienzo. | Satisfactorio |
| **3** | Crear relaciones y configurar multiplicidad. | La relacion muestra origen, destino y multiplicidades correctas. | Satisfactorio |
| **4** | Guardar y recargar el diagrama. | El diagrama se persiste y vuelve a mostrarse completo. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-12: Generar diagramas UML desde imagenes

> **Caso de uso:** CU-12 Generar diagramas UML desde imagenes **ID de Prueba:** TS-CU12-01 **Descripcion:** Validar que el sistema detecte clases, atributos, metodos y relaciones desde una imagen. **Precondiciones:** Usuario Editor con proyecto activo y una imagen de diagrama UML disponible.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Cargar imagen de diagrama UML. | El sistema acepta el archivo de imagen. | Satisfactorio |
| **2** | Ejecutar Imagen a UML. | El motor preprocesa la imagen y extrae informacion. | Satisfactorio |
| **3** | Revisar resultado detectado. | Se identifican clases, atributos, metodos y relaciones. | Satisfactorio |
| **4** | Confirmar generacion. | El sistema dibuja el diagrama en el editor UML. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-13: Importar y exportar modelos UML

> **Caso de uso:** CU-13 Importar y exportar modelos UML **ID de Prueba:** TS-CU13-01 **Descripcion:** Validar interoperabilidad XMI con Enterprise Architect. **Precondiciones:** Usuario Editor u Organizador con proyecto activo.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Importar archivo XML/XMI valido. | El sistema valida formato y convierte a modelo interno. | Satisfactorio |
| **2** | Revisar diagrama importado. | Clases, atributos, metodos, relaciones y multiplicidades se muestran correctamente. | Satisfactorio |
| **3** | Exportar el diagrama a XML/XMI. | El sistema genera archivo compatible con Enterprise Architect. | Satisfactorio |
| **4** | Reimportar el archivo exportado. | El modelo conserva estructura sin duplicados ni perdida de datos. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-14: Validar diagramas UML

> **Caso de uso:** CU-14 Validar diagramas UML **ID de Prueba:** TS-CU14-01 **Descripcion:** Validar analisis de consistencia estructural del diagrama. **Precondiciones:** Diagrama UML abierto en el editor.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Solicitar validacion del diagrama. | El sistema analiza clases, atributos, metodos y relaciones. | Satisfactorio |
| **2** | Validar un diagrama correcto. | El sistema informa que no presenta observaciones. | Satisfactorio |
| **3** | Validar un diagrama con errores. | El sistema muestra errores, advertencias y recomendaciones. | Satisfactorio |
| **4** | Corregir errores y validar nuevamente. | Las observaciones disminuyen o desaparecen. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-15: Transformar modelo UML

> **Caso de uso:** CU-15 Transformar modelo UML **ID de Prueba:** TS-CU15-01 **Descripcion:** Validar transformacion de diagrama UML a modelo intermedio. **Precondiciones:** Proyecto y diagrama UML seleccionados.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Seleccionar proyecto. | El sistema carga diagramas del proyecto. | Satisfactorio |
| **2** | Seleccionar diagrama UML. | El sistema habilita la accion Transformar UML. | Satisfactorio |
| **3** | Ejecutar transformacion. | El motor valida el UML y crea estructura intermedia. | Satisfactorio |
| **4** | Consultar resultado. | El sistema muestra transformacion completada y su identificador. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-16: Generar backend Spring Boot

> **Caso de uso:** CU-16 Generar backend Spring Boot **ID de Prueba:** TS-CU16-01 **Descripcion:** Validar generacion del proyecto backend y sus artefactos descargables. **Precondiciones:** Modelo intermedio generado correctamente.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Seleccionar modelo intermedio disponible. | El sistema habilita Generar backend. | Satisfactorio |
| **2** | Ejecutar generacion Spring Boot. | El generador crea entidades, DTO, repositorios, servicios y controladores. | Satisfactorio |
| **3** | Descargar ZIP generado. | El archivo contiene proyecto Spring Boot, scripts y configuracion PostgreSQL. | Satisfactorio |
| **4** | Ejecutar `.\scripts\run.ps1`. | El backend inicia y expone Swagger en `localhost:8080`. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-17: Generar frontend movil Flutter

> **Caso de uso:** CU-17 Generar frontend movil Flutter **ID de Prueba:** TS-CU17-01 **Descripcion:** Validar generacion del proyecto Flutter conectado al backend. **Precondiciones:** Backend generado o contrato backend disponible.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Ingresar URL base del backend. | El sistema registra `API_BASE_URL` para Flutter. | Satisfactorio |
| **2** | Ejecutar generacion Flutter. | El generador crea modelos Dart, servicios, pantallas, formularios y rutas. | Satisfactorio |
| **3** | Descargar ZIP generado. | El archivo contiene proyecto Flutter ejecutable. | Satisfactorio |
| **4** | Ejecutar `flutter analyze` y `flutter run`. | La app compila, se instala y consume el backend configurado. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio

## Prueba de Caso de Uso CU-18: Ejecutar generacion mediante IA local offline

> **Caso de uso:** CU-18 Ejecutar generacion mediante IA local offline **ID de Prueba:** TS-CU18-01 **Descripcion:** Validar generacion de diagrama desde texto o voz usando IA local. **Precondiciones:** Motor IA local disponible y usuario Editor autenticado.

| Paso | Accion / Entrada | Resultado Esperado | Estado (Satisfactorio / Fallido) |
| --- | --- | --- | --- |
| **1** | Ingresar prompt textual para crear modelo. | El frontend envia solicitud al backend. | Satisfactorio |
| **2** | Procesar solicitud con motor local. | La IA procesa sin depender de API externa. | Satisfactorio |
| **3** | Revisar resultado estructurado. | El sistema devuelve clases, atributos, metodos y relaciones. | Satisfactorio |
| **4** | Confirmar generacion del diagrama. | El modelo se dibuja en el editor UML y se registra el uso de IA. | Satisfactorio |

> **Resultado de la prueba:** Satisfactorio
