# Detalle de diagramas de estado CU01-CU10

Se excluye CU07. Dibujar cada caso con pseudoestado inicial, estados principales, decisiones cuando exista bifurcacion y estado final.

Formato preparado para futura transformacion a VBScript de Enterprise Architect:

- `[*] -> Estado` crea el pseudoestado inicial y una transicion.
- `EstadoA -> EstadoB : evento()` crea una transicion con etiqueta.
- `DecisionX <<choice>> : Texto?` crea un nodo decision/choice con texto visible.
- `Estado -> [*] : evento()` crea el estado final y una transicion.

## CU01. Registrar cuenta de usuario

Marco: `stm CU01 Registrar cuenta de usuario`

Estados:
```text
[*] -> FormularioRegistro
FormularioRegistro -> DatosRecibidos : enviarFormulario()
DatosRecibidos -> DecisionDatosValidos
DecisionDatosValidos <<choice>> : Datos validos?
DecisionDatosValidos -> RegistroRechazado : [datos invalidos]
DecisionDatosValidos -> CorreoConsultado : [datos validos]
CorreoConsultado -> DecisionCorreoDisponible
DecisionCorreoDisponible <<choice>> : Correo disponible?
DecisionCorreoDisponible -> RegistroRechazado : [correo existente]
DecisionCorreoDisponible -> PasswordCifrado : [correo disponible]
PasswordCifrado -> UsuarioPersistido : crearUsuario()
UsuarioPersistido -> RolAsignado : asignarRolEditor()
RolAsignado -> BitacoraRegistrada : registrarAuditoria()
BitacoraRegistrada -> RegistroConfirmado
RegistroConfirmado -> [*]
RegistroRechazado -> FormularioRegistro : corregirDatos()
```

## CU02. Gestionar autenticacion

Estados:
```text
[*] -> NoAutenticado
NoAutenticado -> CredencialesIngresadas : enviarLogin()
CredencialesIngresadas -> UsuarioConsultado : buscarUsuario()
UsuarioConsultado -> DecisionCredenciales
DecisionCredenciales <<choice>> : Credenciales validas?
DecisionCredenciales -> AutenticacionRechazada : [credenciales invalidas]
DecisionCredenciales -> AutenticacionRechazada : [usuario inactivo]
DecisionCredenciales -> TokenEmitido : [credenciales validas]
TokenEmitido -> SesionActiva : guardarJwt()
SesionActiva -> SesionCerrada : cerrarSesion()
AutenticacionRechazada -> NoAutenticado : reintentar()
SesionCerrada -> [*]
```

## CU03. Gestionar perfil propio

Estados:
```text
[*] -> PerfilSolicitado
PerfilSolicitado -> DecisionSesion
DecisionSesion <<choice>> : Sesion valida?
DecisionSesion -> SesionExpirada : [token invalido]
DecisionSesion -> PerfilCargado : [token valido]
PerfilCargado -> EdicionPerfil : modificarDatos()
EdicionPerfil -> UsuarioConsultado : guardarCambios()
UsuarioConsultado -> DecisionUsuarioExiste
DecisionUsuarioExiste <<choice>> : Usuario existe?
DecisionUsuarioExiste -> ActualizacionRechazada : [usuario no encontrado]
DecisionUsuarioExiste -> PerfilActualizado : [usuario encontrado]
PerfilActualizado -> BitacoraRegistrada : auditarCambio()
BitacoraRegistrada -> PerfilMostrado
PerfilMostrado -> [*]
SesionExpirada -> [*]
ActualizacionRechazada -> EdicionPerfil : corregir()
```

## CU04. Gestionar usuarios y roles globales

Estados:
```text
[*] -> UsuariosListados
UsuariosListados -> UsuarioSeleccionado : seleccionarUsuario()
UsuarioSeleccionado -> CambioPreparado : cambiarEstadoDatosRol()
CambioPreparado -> DecisionPermisos
DecisionPermisos <<choice>> : Tiene permisos?
DecisionPermisos -> CambioRechazado : [sin permisos]
DecisionPermisos -> UsuarioConsultado : [con permisos]
UsuarioConsultado -> DecisionUsuarioObjetivo
DecisionUsuarioObjetivo <<choice>> : Usuario objetivo existe?
DecisionUsuarioObjetivo -> CambioRechazado : [usuario no existe]
DecisionUsuarioObjetivo -> UsuarioActualizado : [usuario existe]
UsuarioActualizado -> BitacoraRegistrada : registrarAuditoria()
BitacoraRegistrada -> UsuariosListados
CambioRechazado -> UsuariosListados
UsuariosListados -> [*] : cerrarGestion()
```

## CU05. Consultar reportes del proyecto

Estados:
```text
[*] -> ReporteSolicitado
ReporteSolicitado -> MembresiaVerificada : validarAcceso()
MembresiaVerificada -> DecisionAccesoReporte
DecisionAccesoReporte <<choice>> : Puede consultar reportes?
DecisionAccesoReporte -> ReporteRechazado : [sin membresia]
DecisionAccesoReporte -> DatosFiltrados : [con membresia]
DatosFiltrados -> DecisionDatosReporte
DecisionDatosReporte <<choice>> : Hay datos para reporte?
DecisionDatosReporte -> EstadoVacioMostrado : [sin datos]
DecisionDatosReporte -> IndicadoresCalculados : [datos disponibles]
IndicadoresCalculados -> ReporteMostrado
EstadoVacioMostrado -> ReporteMostrado
ReporteMostrado -> [*]
ReporteRechazado -> [*]
```

## CU06. Consultar bitacora del proyecto

Estados:
```text
[*] -> BitacoraSolicitada
BitacoraSolicitada -> PermisosVerificados : validarMembresia()
PermisosVerificados -> DecisionAccesoBitacora
DecisionAccesoBitacora <<choice>> : Puede consultar bitacora?
DecisionAccesoBitacora -> BitacoraRechazada : [sin permisos]
DecisionAccesoBitacora -> FiltrosAplicados : [con permisos]
FiltrosAplicados -> EventosConsultados
EventosConsultados -> DecisionEventos
DecisionEventos <<choice>> : Hay eventos registrados?
DecisionEventos -> SinEventos : [sin registros]
DecisionEventos -> EventosEncontrados : [existen registros]
EventosEncontrados -> BitacoraMostrada
SinEventos -> BitacoraMostrada
BitacoraMostrada -> [*]
BitacoraRechazada -> [*]
```

## CU08. Gestionar proyectos de desarrollo

Estados:
```text
[*] -> ListaProyectos
ListaProyectos -> FormularioProyecto : crearEditar()
FormularioProyecto -> DecisionDatosProyecto
DecisionDatosProyecto <<choice>> : Datos del proyecto validos?
DecisionDatosProyecto -> ProyectoRechazado : [datos invalidos]
DecisionDatosProyecto -> ProyectoPersistiendo : [datos validos]
ProyectoPersistiendo -> DecisionPersistencia
DecisionPersistencia <<choice>> : Proyecto persistido?
DecisionPersistencia -> ProyectoRechazado : [error persistencia]
DecisionPersistencia -> ProyectoCreado : [persistido]
ProyectoCreado -> MiembroOrganizadorAsignado
MiembroOrganizadorAsignado -> ProyectoActivo
ProyectoActivo -> ProyectoArchivado : archivar()
ProyectoArchivado -> [*]
ProyectoRechazado -> FormularioProyecto : corregir()
ProyectoActivo -> [*] : cerrarVista()
```

## CU09. Gestionar integrantes y permisos del proyecto

Estados:
```text
[*] -> IntegrantesListados
IntegrantesListados -> IntegranteSeleccionado : seleccionar()
IntegranteSeleccionado -> DecisionOperacionIntegrante
DecisionOperacionIntegrante <<choice>> : Que operacion de integrante?
DecisionOperacionIntegrante -> IntegranteExistente : [usuario ya es integrante]
DecisionOperacionIntegrante -> IntegranteInvitado : [nuevo integrante]
DecisionOperacionIntegrante -> PermisoEditado : [modificar permiso]
DecisionOperacionIntegrante -> IntegranteRemovido : [eliminar miembro]
PermisoEditado -> DecisionOrganizador
DecisionOrganizador <<choice>> : Permiso de organizador valido?
DecisionOrganizador -> CambioRechazado : [organizador insuficiente]
DecisionOrganizador -> PermisoPersistido : [permiso valido]
IntegranteInvitado -> MembresiaActiva
MembresiaActiva -> IntegrantesListados
IntegranteExistente -> IntegrantesListados
PermisoPersistido -> IntegrantesListados
IntegranteRemovido -> IntegrantesListados
CambioRechazado -> IntegrantesListados
IntegrantesListados -> [*] : cerrarGestion()
```

## CU10. Gestionar versiones y cambios del proyecto

Estados:
```text
[*] -> ModeloActual
ModeloActual -> VersionSolicitada : guardarVersion()
VersionSolicitada -> DecisionSnapshot
DecisionSnapshot <<choice>> : Snapshot valido?
DecisionSnapshot -> VersionRechazada : [snapshot invalido]
DecisionSnapshot -> ProyectoConsultado : [snapshot valido]
ProyectoConsultado -> DecisionProyecto
DecisionProyecto <<choice>> : Proyecto existe?
DecisionProyecto -> VersionRechazada : [proyecto no encontrado]
DecisionProyecto -> SnapshotConstruido : [proyecto encontrado]
SnapshotConstruido -> VersionPersistida
VersionPersistida -> HistorialActualizado
HistorialActualizado -> ModeloActual
ModeloActual -> VersionRestaurada : restaurarSnapshot()
VersionRestaurada -> ModeloActual
VersionRechazada -> ModeloActual
ModeloActual -> [*] : cerrarWorkspace()
```
