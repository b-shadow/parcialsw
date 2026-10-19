# Fase 2 - Casos de uso

## CU-01 Registrar cuenta de usuario

Actor principal: Editor.

Precondiciones:

- El usuario no tiene cuenta activa con el correo ingresado.

Flujo principal:

1. El usuario abre el formulario de registro.
2. Ingresa nombre, correo y contrasena.
3. El sistema valida datos.
4. El sistema cifra la contrasena.
5. El sistema crea la cuenta con rol inicial Editor.
6. El sistema registra la accion en bitacora.

Postcondiciones:

- Usuario registrado y disponible para autenticacion.

## CU-02 Gestionar autenticacion

Actor principal: Editor, Administrador u Organizador.

Flujo principal:

1. Usuario ingresa correo y contrasena.
2. Backend valida credenciales.
3. Backend emite JWT.
4. Frontend almacena token de sesion.
5. Sistema habilita rutas segun permisos.

Postcondiciones:

- Sesion autenticada activa.

## CU-03 Gestionar perfil propio

Actor principal: Usuario autenticado.

Flujo principal:

1. Usuario abre su perfil.
2. Consulta sus datos.
3. Modifica informacion permitida.
4. Sistema valida y guarda cambios.
5. Sistema registra evento.

## CU-04 Gestionar usuarios y roles globales

Actor principal: Administrador.

Flujo principal:

1. Administrador consulta usuarios.
2. Selecciona usuario.
3. Cambia estado o rol global.
4. Sistema valida permisos administrativos.
5. Sistema aplica cambio y registra bitacora.

## CU-05 Consultar reportes

Actor principal: Administrador u Organizador.

Flujo principal:

1. Actor abre panel de reportes.
2. Sistema filtra informacion segun permisos.
3. Sistema muestra indicadores de proyectos, actividad, cambios y generaciones.

## CU-06 Consultar bitacora

Actor principal: Administrador u Organizador.

Flujo principal:

1. Actor solicita bitacora.
2. Sistema aplica filtros por rol y proyecto.
3. Sistema muestra acciones, usuarios, fechas y resultados.

## CU-07 Consultar manual guiado

Actor principal: Usuario autenticado.

Flujo principal:

1. Usuario abre ayuda contextual.
2. Sistema muestra guia segun modulo actual.
3. Usuario navega pasos del manual.

## CU-08 Gestionar proyectos de desarrollo

Actor principal: Editor.

Flujo principal:

1. Editor crea proyecto.
2. Sistema valida datos.
3. Sistema crea proyecto.
4. Sistema registra al creador como Organizador interno.
5. Sistema muestra el entorno del proyecto.

## CU-09 Gestionar integrantes y permisos

Actor principal: Organizador.

Flujo principal:

1. Organizador abre administracion de integrantes.
2. Invita usuario o modifica permisos existentes.
3. Sistema valida rol interno.
4. Sistema guarda permisos.
5. Sistema registra cambio en bitacora.

## CU-10 Gestionar versiones y cambios

Actor principal: Organizador o Editor con permiso.

Flujo principal:

1. Actor guarda una version del modelo.
2. Sistema registra descripcion, usuario y fecha.
3. Sistema conserva estado del modelo.
4. Actor consulta historial o restaura version.

## CU-11 Crear y editar diagramas de clases UML

Actor principal: Editor.

Flujo principal:

1. Editor abre el editor UML.
2. Crea clases, atributos, metodos y relaciones.
3. Frontend envia eventos al backend.
4. Backend valida permisos.
5. Backend persiste cambios.
6. Backend sincroniza con usuarios conectados.

## CU-12 Generar diagramas UML desde imagenes

Actor principal: Editor.

Flujo principal:

1. Editor carga imagen de diagrama.
2. Sistema preprocesa imagen.
3. IA/OCR detecta clases, atributos, metodos y relaciones.
4. Sistema construye modelo interno.
5. Usuario revisa y confirma.

## CU-13 Importar y exportar modelos UML

Actor principal: Editor u Organizador.

Flujo principal:

1. Actor selecciona importar o exportar XMI.
2. Sistema valida formato.
3. Sistema transforma entre XMI y modelo interno.
4. Sistema registra operacion.

## CU-14 Validar diagramas UML

Actor principal: Editor.

Flujo principal:

1. Editor solicita validacion.
2. Sistema analiza estructura.
3. IA local genera observaciones.
4. Sistema muestra errores, advertencias y recomendaciones.

## CU-15 Transformar modelo UML

Actor principal: Editor con permiso.

Flujo principal:

1. Actor solicita transformacion.
2. Sistema valida modelo UML.
3. Motor convierte UML en estructura intermedia.
4. Sistema guarda resultado de transformacion.

## CU-16 Generar backend Spring Boot

Actor principal: Editor con permiso.

Flujo principal:

1. Actor selecciona modelo/version.
2. Sistema ejecuta generador determinista.
3. Generador crea entidades, DTO, repositorios, servicios y controladores.
4. Sistema valida estructura.
5. Sistema registra artefacto generado.

## CU-17 Generar frontend movil Flutter

Actor principal: Editor con permiso.

Flujo principal:

1. Actor selecciona modelo y contrato backend.
2. Sistema interpreta entidades y endpoints.
3. Generador crea modelos Dart, servicios, pantallas, formularios y rutas.
4. Sistema valida proyecto generado.
5. Sistema registra artefacto generado.

## CU-18 Ejecutar generacion mediante IA local offline

Actor principal: Editor.

Flujo principal:

1. Actor solicita asistencia IA.
2. Backend envia solicitud al motor local.
3. Motor IA procesa sin API externa.
4. Sistema devuelve resultado estructurado.
5. Sistema registra uso de IA.

