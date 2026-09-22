# Pruebas unitarias principales

Estas pruebas se enfocan en funciones, servicios y transformadores internos del sistema. El objetivo es cubrir logica critica con Pytest en backend/IA y Vitest o pruebas equivalentes en frontend.

## Prueba Unitaria: PU-BACK-01

> **Caso de Uso Relacionado:** CU-01 Registrar cuenta de usuario **Modulo / Archivo:** Backend — `backend/app/modules/acceso_usuarios/services/user_service.py` **Funcion / Metodo Evaluado:** `create_user()` **Herramienta:** Pytest **Descripcion:** Comprobar que el servicio cree usuario con correo unico, hash de contrasena y rol inicial.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | `nombre="Editor UML"`, `correo="editor@test.com"`, `password="Segura123"` y repositorio sin usuario previo. |
| **Resultado Esperado (Assert):** | Usuario creado, password no almacenado en texto plano, rol `Editor` y estado `active`. |
| **Resultado Obtenido:** | Usuario creado con hash y datos normalizados. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-02

> **Caso de Uso Relacionado:** CU-02 Gestionar autenticacion **Modulo / Archivo:** Backend — `backend/app/core/security` **Funcion / Metodo Evaluado:** `verify_password()` / `create_access_token()` **Herramienta:** Pytest **Descripcion:** Verificar validacion de credenciales y emision de token JWT.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Password correcto, hash almacenado y payload con `sub` del usuario. |
| **Resultado Esperado (Assert):** | La contrasena se valida correctamente y el token contiene identificador del usuario. |
| **Resultado Obtenido:** | Token generado y validacion positiva. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-03

> **Caso de Uso Relacionado:** CU-03 Gestionar perfil propio **Modulo / Archivo:** Backend — `backend/app/modules/acceso_usuarios/services/user_service.py` **Funcion / Metodo Evaluado:** `update_profile()` **Herramienta:** Pytest **Descripcion:** Comprobar que solo se actualicen campos permitidos del perfil.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Usuario autenticado y payload con nombre nuevo, correo sin duplicar y campos no permitidos. |
| **Resultado Esperado (Assert):** | Se actualizan campos permitidos y se ignoran o rechazan campos restringidos. |
| **Resultado Obtenido:** | Perfil actualizado sin alterar rol global ni estado. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-04

> **Caso de Uso Relacionado:** CU-04 Gestionar usuarios y roles globales **Modulo / Archivo:** Backend — `backend/app/modules/acceso_usuarios/services/user_service.py` **Funcion / Metodo Evaluado:** `update_user_role()` **Herramienta:** Pytest **Descripcion:** Validar que solo un administrador pueda cambiar roles globales.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Usuario administrador, usuario destino y rol nuevo `Organizador`. |
| **Resultado Esperado (Assert):** | Cambio persistido y error de permiso si el actor no es administrador. |
| **Resultado Obtenido:** | Rol actualizado con control de permisos. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-FRONT-01

> **Caso de Uso Relacionado:** CU-05 Consultar reportes **Modulo / Archivo:** Frontend — `frontend/src/modules/gestion_acceso_usuarios/pages/ReportsPage.tsx` **Funcion / Metodo Evaluado:** Renderizado de indicadores **Herramienta:** Vitest **Descripcion:** Verificar que los datos de reportes se agrupen y muestren sin dejar pantalla vacia.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Mock de proyectos, diagramas, usuarios y generaciones. |
| **Resultado Esperado (Assert):** | Se renderizan tarjetas de actividad, proyectos, colaboradores y generaciones. |
| **Resultado Obtenido:** | Indicadores visibles y consistentes. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-05

> **Caso de Uso Relacionado:** CU-06 Consultar bitacora **Modulo / Archivo:** Backend — `backend/app/modules/*/services` **Funcion / Metodo Evaluado:** Filtro de eventos de auditoria **Herramienta:** Pytest **Descripcion:** Verificar que la bitacora respete filtros de proyecto, usuario y fecha.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Lista de eventos con proyectos y usuarios diferentes. |
| **Resultado Esperado (Assert):** | Solo se devuelven eventos que coinciden con los filtros. |
| **Resultado Obtenido:** | Eventos filtrados correctamente. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-FRONT-02

> **Caso de Uso Relacionado:** CU-07 Consultar manual guiado **Modulo / Archivo:** Frontend — `frontend/src/shared/components/AssistantWidget.tsx` **Funcion / Metodo Evaluado:** Motor de respuestas del asistente **Herramienta:** Vitest **Descripcion:** Validar respuestas contextuales del asistente sobre acciones del sistema.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Pregunta: `Donde genero diagramas mediante fotos?` |
| **Resultado Esperado (Assert):** | Respuesta menciona editor UML, opcion Imagen a UML y confirmacion del diagrama. |
| **Resultado Obtenido:** | El asistente devuelve guia contextual. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-06

> **Caso de Uso Relacionado:** CU-08 Gestionar proyectos de desarrollo **Modulo / Archivo:** Backend — `backend/app/modules/proyectos_colaboracion/services` **Funcion / Metodo Evaluado:** `create_project()` **Herramienta:** Pytest **Descripcion:** Comprobar que el creador del proyecto quede como Organizador interno.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Datos de proyecto y usuario Editor creador. |
| **Resultado Esperado (Assert):** | Proyecto creado y membresia interna con rol Organizador. |
| **Resultado Obtenido:** | Proyecto y colaborador inicial persistidos. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-07

> **Caso de Uso Relacionado:** CU-09 Gestionar integrantes y permisos **Modulo / Archivo:** Backend — `backend/app/modules/proyectos_colaboracion/services` **Funcion / Metodo Evaluado:** `add_collaborator()` **Herramienta:** Pytest **Descripcion:** Verificar validacion de rol interno al agregar colaboradores.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Actor Organizador, usuario invitado y rol `Editor`. |
| **Resultado Esperado (Assert):** | Colaborador agregado; actor sin permiso recibe error. |
| **Resultado Obtenido:** | Permisos aplicados correctamente. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-BACK-08

> **Caso de Uso Relacionado:** CU-10 Gestionar versiones y cambios **Modulo / Archivo:** Backend — `backend/app/modules/modelado_uml/services` **Funcion / Metodo Evaluado:** `save_version()` **Herramienta:** Pytest **Descripcion:** Validar snapshot del modelo con usuario, fecha y descripcion.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Diagrama UML con clases y descripcion de version. |
| **Resultado Esperado (Assert):** | Version creada con snapshot completo del modelo. |
| **Resultado Obtenido:** | Historial registra version consultable. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-UML-01

> **Caso de Uso Relacionado:** CU-11 Crear y editar diagramas de clases UML **Modulo / Archivo:** Frontend — `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx` **Funcion / Metodo Evaluado:** Gestion de relaciones y multiplicidad **Herramienta:** Vitest **Descripcion:** Comprobar que una relacion almacene multiplicidad de origen y destino sin copiarla como atributo.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Relacion `Curso -> Tema` con origen `1` y destino `*`. |
| **Resultado Esperado (Assert):** | La relacion conserva multiplicidades y las clases no agregan atributos `0..*`, `1` o `*`. |
| **Resultado Obtenido:** | Multiplicidades guardadas en la relacion. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-IA-01

> **Caso de Uso Relacionado:** CU-12 Generar diagramas UML desde imagenes **Modulo / Archivo:** IA — `ai-engine/ai_engine/preprocessing/image_uml_detector.py` **Funcion / Metodo Evaluado:** `detect_uml_from_image()` **Herramienta:** Pytest **Descripcion:** Validar deteccion minima de clases, atributos, metodos y relaciones desde imagen de prueba.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Imagen con clases `Estudiante`, `Curso` e `Inscripcion`. |
| **Resultado Esperado (Assert):** | Modelo con tres clases, atributos principales y relacion asociativa. |
| **Resultado Obtenido:** | Estructura UML detectada y normalizada. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-XMI-01

> **Caso de Uso Relacionado:** CU-13 Importar y exportar modelos UML **Modulo / Archivo:** Backend — `backend/app/modules/modelado_uml/engine` **Funcion / Metodo Evaluado:** Parser/exportador XMI **Herramienta:** Pytest **Descripcion:** Comprobar que el XMI conserve atributos, association class y multiplicidades.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | XML/XMI con `Estudiante`, `Curso`, `Inscripcion` y relacion many-to-many. |
| **Resultado Esperado (Assert):** | Modelo interno con association class y exportacion sin atributos duplicados de multiplicidad. |
| **Resultado Obtenido:** | Importacion/exportacion estable. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-UML-02

> **Caso de Uso Relacionado:** CU-14 Validar diagramas UML **Modulo / Archivo:** Backend — `backend/app/modules/modelado_uml/validators` **Funcion / Metodo Evaluado:** `validate_diagram()` **Herramienta:** Pytest **Descripcion:** Validar deteccion de errores, advertencias y recomendaciones.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Diagrama con clase sin nombre, relacion incompleta y diagrama correcto. |
| **Resultado Esperado (Assert):** | Errores para datos invalidos y lista vacia para diagrama correcto. |
| **Resultado Obtenido:** | Observaciones clasificadas correctamente. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-GEN-01

> **Caso de Uso Relacionado:** CU-15 Transformar modelo UML **Modulo / Archivo:** Backend — `backend/app/modules/generacion_software/services/generation_service.py` **Funcion / Metodo Evaluado:** `transform_uml()` **Herramienta:** Pytest **Descripcion:** Comprobar conversion de UML a modelo intermedio.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Diagrama con clases, atributos, metodos, relaciones y multiplicidades. |
| **Resultado Esperado (Assert):** | Modelo intermedio con entidades, campos y relaciones normalizadas. |
| **Resultado Obtenido:** | Transformacion completada con identificador. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-GEN-02

> **Caso de Uso Relacionado:** CU-16 Generar backend Spring Boot **Modulo / Archivo:** Backend — `backend/app/modules/generacion_software/backend_generator/templates/spring_boot_templates.py` **Funcion / Metodo Evaluado:** Renderizado de plantillas Spring Boot **Herramienta:** Pytest **Descripcion:** Validar que el backend generado incluya CRUD, DTO, relaciones y scripts ejecutables.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Modelo intermedio con `Estudiante`, `Curso`, `Tema` e `Inscripcion`. |
| **Resultado Esperado (Assert):** | Proyecto con entidades JPA, controladores REST, `docker-compose.yml`, `scripts/run.ps1` y PostgreSQL en `55432`. |
| **Resultado Obtenido:** | Artefactos generados correctamente. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-GEN-03

> **Caso de Uso Relacionado:** CU-17 Generar frontend movil Flutter **Modulo / Archivo:** Backend — `backend/app/modules/generacion_software/flutter_generator/templates/flutter_templates.py` **Funcion / Metodo Evaluado:** Renderizado de pantallas Flutter **Herramienta:** Pytest **Descripcion:** Validar que Flutter genere formularios, selectores de relaciones y fechas.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Modelo con campos `Date`, `Double`, `String` y relaciones `estudianteId`, `cursoId`. |
| **Resultado Esperado (Assert):** | Formularios con `showDatePicker`, `DropdownButtonFormField`, `API_BASE_URL` y sin overflow de identificadores. |
| **Resultado Obtenido:** | Proyecto Flutter analizable y ejecutable. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-IA-02

> **Caso de Uso Relacionado:** CU-18 Ejecutar generacion mediante IA local offline **Modulo / Archivo:** IA — `ai-engine/ai_engine/inference/local_engine.py` **Funcion / Metodo Evaluado:** `generate_uml_from_prompt()` **Herramienta:** Pytest **Descripcion:** Comprobar que un prompt textual produzca un modelo UML estructurado sin API externa.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | `Crear sistema academico con Estudiante, Curso e Inscripcion` |
| **Resultado Esperado (Assert):** | Salida JSON con clases, atributos, metodos y relaciones coherentes. |
| **Resultado Obtenido:** | Modelo generado por motor local. |
| **Estado:** | **PASSED** |

## Prueba Unitaria: PU-FRONT-03

> **Caso de Uso Relacionado:** CU-16/CU-17 Generacion de software **Modulo / Archivo:** Frontend — `frontend/src/modules/transformacion_generacion_software/pages/GenerationPage.tsx` **Funcion / Metodo Evaluado:** Flujo de seleccion proyecto-diagrama-generacion **Herramienta:** Vitest **Descripcion:** Verificar que primero se elija proyecto, luego diagrama, luego transformacion, backend y frontend.

| Campo | Detalle |
| --- | --- |
| **Entrada (Input / Mock):** | Proyecto con diagrama `clases` y estados de generacion vacios. |
| **Resultado Esperado (Assert):** | El boton backend se habilita tras transformar UML y el frontend tras detectar backend/API. |
| **Resultado Obtenido:** | Secuencia de botones y estados correcta. |
| **Estado:** | **PASSED** |
