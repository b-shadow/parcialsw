# Detalle de diagramas de secuencia CU01-CU10

Se excluye CU07. Version v2: usa nombres semanticos para diagramar. Estilo: actor a la izquierda, UI, cliente, controlador, servicio, repositorio y base de datos. Usar flecha continua para llamadas y punteada para retornos.

Los fragmentos `alt [condicion] ... end` estan integrados en el flujo principal. En Enterprise Architect se dibujan como Combined Fragment con operador `alt` exactamente en esa posicion; al cerrar `end`, el flujo continua con la siguiente linea.

## CU01. Registrar cuenta de usuario

Marco: `sd CU01 Registrar cuenta de usuario`

Lifelines:
```text
Usuario
UI::RegistroUsuario
Cliente::AutenticacionClient
Controlador::AutenticacionController
Servicio::AutenticacionService
Repositorio::UsuarioRepository
Repositorio::RolRepository
Servicio::AuditoriaService
DB::BaseDatos
```

### Flujo principal
```text
Usuario -> RegistroUsuario: enviarRegistro()
RegistroUsuario -> RegistroUsuario: validarFormulario()
alt [datos invalidos]
RegistroUsuario --> Usuario: mostrarError()
end
RegistroUsuario -> AutenticacionClient: register()
AutenticacionClient -> AutenticacionController: register()
AutenticacionController -> AutenticacionService: register()
AutenticacionService -> UsuarioRepository: get_by_email()
UsuarioRepository -> BaseDatos: select_users()
BaseDatos --> UsuarioRepository: UsuarioOrNull
alt [correo ya registrado]
AutenticacionService --> AutenticacionController: errorValidacion()
AutenticacionController --> RegistroUsuario: mostrarError()
end
AutenticacionService -> AutenticacionService: hash_password()
AutenticacionService -> RolRepository: get_by_name()
RolRepository -> BaseDatos: select_roles()
AutenticacionService -> UsuarioRepository: add()
UsuarioRepository -> BaseDatos: insert_users()
AutenticacionService -> AuditoriaService: record()
AuditoriaService -> BaseDatos: insert_audit_logs()
AutenticacionService --> AutenticacionController: Usuario
AutenticacionController --> AutenticacionClient: UsuarioResponse
AutenticacionClient --> RegistroUsuario: usuario registrado
```

## CU02. Gestionar autenticacion

Marco: `sd CU02 Gestionar autenticacion`

Lifelines:
```text
Usuario
UI::Login
Cliente::AutenticacionClient
Controlador::AutenticacionController
Servicio::AutenticacionService
Repositorio::UsuarioRepository
Servicio::TokenService
Servicio::AuditoriaService
DB::BaseDatos
```

### Flujo principal
```text
Usuario -> Login: ingresarCredenciales()
Login -> AutenticacionClient: login()
AutenticacionClient -> AutenticacionController: login()
AutenticacionController -> AutenticacionService: login()
AutenticacionService -> UsuarioRepository: get_by_email()
UsuarioRepository -> BaseDatos: select_users()
BaseDatos --> UsuarioRepository: UsuarioOrNull
AutenticacionService -> AutenticacionService: verify_password()
alt [credenciales invalidas]
AutenticacionService --> AutenticacionController: errorAutenticacion()
AutenticacionController --> Login: mostrarError()
end
alt [usuario inactivo]
AutenticacionService --> AutenticacionController: errorAutenticacion()
AutenticacionController --> Login: mostrarError()
end
AutenticacionService -> TokenService: create_access_token()
TokenService --> AutenticacionService: token
AutenticacionService -> AuditoriaService: record()
AuditoriaService -> BaseDatos: insert_audit_logs()
AutenticacionService --> AutenticacionController: TokenResponse
AutenticacionController --> AutenticacionClient: TokenResponse
AutenticacionClient --> Login: access_token
Login -> Login: guardarSesion()
```

## CU03. Gestionar perfil propio

Marco: `sd CU03 Gestionar perfil propio`

Lifelines:
```text
Usuario
UI::PerfilUsuario
Cliente::UsuarioClient
Controlador::AutenticacionController
Controlador::UsuariosController
Servicio::UsuarioService
Repositorio::UsuarioRepository
Servicio::AuditoriaService
DB::BaseDatos
```

### Flujo principal
```text
Usuario -> PerfilUsuario: abrirPerfil()
PerfilUsuario -> UsuarioClient: me()
UsuarioClient -> AutenticacionController: me()
alt [token invalido o sesion expirada]
AutenticacionController --> UsuarioClient: errorAutorizacion()
UsuarioClient --> PerfilUsuario: redirigirLogin()
end
AutenticacionController --> UsuarioClient: UsuarioResponse
Usuario -> PerfilUsuario: actualizarDatos()
PerfilUsuario -> UsuarioClient: updateUser()
UsuarioClient -> UsuariosController: update_user()
UsuariosController -> UsuarioService: update_user()
UsuarioService -> UsuarioRepository: get_by_id()
UsuarioRepository -> BaseDatos: select_users()
UsuarioRepository --> UsuarioService: UsuarioOrNull
alt [usuario no encontrado]
UsuarioService --> UsuariosController: errorNoEncontrado()
UsuariosController --> PerfilUsuario: mostrarError()
end
UsuarioService -> UsuarioRepository: update()
UsuarioRepository -> BaseDatos: update_users()
UsuarioService -> AuditoriaService: record()
AuditoriaService -> BaseDatos: insert_audit_logs()
UsuarioService --> UsuariosController: Usuario
UsuariosController --> PerfilUsuario: UsuarioResponse
```

## CU04. Gestionar usuarios y roles globales

Marco: `sd CU04 Gestionar usuarios y roles globales`

Lifelines:
```text
Administrador
UI::GestionUsuarios
Cliente::UsuarioClient
Controlador::UsuariosController
Servicio::UsuarioService
Repositorio::UsuarioRepository
Servicio::AuditoriaService
DB::BaseDatos
```

### Flujo principal
```text
Administrador -> GestionUsuarios: consultarUsuarios()
GestionUsuarios -> UsuarioClient: list()
UsuarioClient -> UsuariosController: list_users()
UsuariosController -> UsuarioService: list_users()
UsuarioService -> UsuarioRepository: list()
UsuarioRepository -> BaseDatos: select_users()
BaseDatos --> UsuarioRepository: List<Usuario>
UsuariosController --> GestionUsuarios: List<UsuarioResponse>
Administrador -> GestionUsuarios: cambiarEstado()
GestionUsuarios -> UsuarioClient: updateUser()
UsuarioClient -> UsuariosController: update_user()
UsuariosController -> UsuarioService: validarPermisos()
alt [sin permisos de administracion]
UsuarioService --> UsuariosController: errorAutorizacion()
UsuariosController --> GestionUsuarios: mostrarError()
end
UsuariosController -> UsuarioService: update_user()
UsuarioService -> UsuarioRepository: get_by_id()
UsuarioRepository --> UsuarioService: UsuarioOrNull
alt [usuario objetivo no existe]
UsuarioService --> UsuariosController: errorNoEncontrado()
UsuariosController --> GestionUsuarios: mostrarError()
end
UsuarioService -> BaseDatos: update_users()
UsuarioService -> AuditoriaService: record()
AuditoriaService -> BaseDatos: insert_audit_logs()
```

## CU05. Consultar reportes del proyecto

Marco: `sd CU05 Consultar reportes del proyecto`

Lifelines:
```text
Usuario
UI::Reportes
Cliente::ProyectoClient
Cliente::ModeladoUMLClient
Cliente::GeneracionClient
Controlador::ProyectosController
Controlador::ModeladoUMLController
Controlador::GeneracionController
Servicio::ProyectoService
Repositorio::ProyectoRepository
Repositorio::MiembroProyectoRepository
Servicio::ModeladoUMLService
Repositorio::ModeloUMLRepository
Repositorio::GeneracionRepository
DB::BaseDatos
```

### Flujo principal
```text
Usuario -> Reportes: abrirReportes()
Reportes -> ProyectoClient: list()
ProyectoClient -> ProyectosController: list_projects()
ProyectosController -> ProyectoService: list_projects()
ProyectoService -> MiembroProyectoRepository: get_membership()
alt [sin membresia del proyecto]
ProyectoService --> ProyectosController: errorAutorizacion()
ProyectosController --> Reportes: mostrarError()
end
ProyectoService -> ProyectoRepository: list_for_user()
ProyectoRepository -> BaseDatos: select_projects()
ProyectoRepository --> ProyectoService: List<Proyecto>
Reportes -> ModeladoUMLClient: listDiagrams()
ModeladoUMLClient -> ModeladoUMLController: list_diagrams()
ModeladoUMLController -> ModeladoUMLService: list_diagrams()
ModeladoUMLService -> ModeloUMLRepository: list_diagrams_by_project()
ModeloUMLRepository -> BaseDatos: select_uml_diagrams()
ModeloUMLRepository --> ModeladoUMLService: List<DiagramaUML>
alt [proyecto sin datos disponibles]
Reportes -> Reportes: mostrarEstadoVacio()
end
Reportes -> GeneracionClient: consultarResultados()
GeneracionClient -> GeneracionRepository: get_transformation()
GeneracionRepository -> BaseDatos: select_transformations()
Reportes -> Reportes: calcularIndicadores()
```

## CU06. Consultar bitacora del proyecto

Marco: `sd CU06 Consultar bitacora del proyecto`

Lifelines:
```text
Organizador
UI::Reportes
Controlador::ProyectosController
Servicio::ProyectoService
Repositorio::MiembroProyectoRepository
Servicio::AuditoriaService
Repositorio::AuditoriaRepository
DB::BaseDatos
```

### Flujo principal
```text
Organizador -> Reportes: consultarActividad()
Reportes -> ProyectosController: get_project()
ProyectosController -> ProyectoService: get_project()
ProyectoService -> MiembroProyectoRepository: get_membership()
MiembroProyectoRepository -> BaseDatos: select_project_members()
MiembroProyectoRepository --> ProyectoService: MiembroOrNull
alt [sin permisos para consultar bitacora]
ProyectoService --> ProyectosController: errorAutorizacion()
ProyectosController --> Reportes: mostrarError()
end
Reportes -> AuditoriaService: consultarBitacora()
AuditoriaService -> AuditoriaRepository: list_by_project()
AuditoriaRepository -> BaseDatos: select_audit_logs()
BaseDatos --> AuditoriaRepository: List<Auditoria>
alt [bitacora vacia]
AuditoriaService --> Reportes: mostrarEstadoVacio()
end
AuditoriaService --> Reportes: acciones, usuario, fecha, modulo
```

## CU08. Gestionar proyectos de desarrollo

Marco: `sd CU08 Gestionar proyectos de desarrollo`

Lifelines:
```text
Editor
UI::Proyectos
Cliente::ProyectoClient
Controlador::ProyectosController
Servicio::ProyectoService
Repositorio::ProyectoRepository
Repositorio::MiembroProyectoRepository
Servicio::AuditoriaService
DB::BaseDatos
```

### Flujo principal
```text
Editor -> Proyectos: crearProyecto()
Proyectos -> Proyectos: validarFormulario()
alt [nombre o datos invalidos]
Proyectos --> Editor: mostrarError()
end
Proyectos -> ProyectoClient: create()
ProyectoClient -> ProyectosController: create_project()
ProyectosController -> ProyectoService: create_project()
ProyectoService -> ProyectoRepository: add()
ProyectoRepository -> BaseDatos: insert_projects()
alt [error al persistir proyecto]
BaseDatos --> ProyectoRepository: errorPersistencia()
ProyectoService --> ProyectosController: errorPersistencia()
ProyectosController --> Proyectos: mostrarError()
end
ProyectoService -> MiembroProyectoRepository: add()
MiembroProyectoRepository -> BaseDatos: insert_project_members()
ProyectoService -> AuditoriaService: record()
AuditoriaService -> BaseDatos: insert_audit_logs()
ProyectoService --> ProyectosController: Proyecto
ProyectosController --> Proyectos: ProyectoResponse
```

## CU09. Gestionar integrantes y permisos del proyecto

Marco: `sd CU09 Gestionar integrantes y permisos del proyecto`

Lifelines:
```text
Organizador
UI::GestionIntegrantesPermisos
Cliente::ProyectoClient
Controlador::ProyectosController
Servicio::ProyectoService
Repositorio::MiembroProyectoRepository
DB::BaseDatos
```

### Flujo principal
```text
Organizador -> GestionIntegrantesPermisos: abrirIntegrantes()
GestionIntegrantesPermisos -> ProyectoClient: listMembers()
ProyectoClient -> ProyectosController: list_members()
ProyectosController -> ProyectoService: list_members()
ProyectoService -> MiembroProyectoRepository: list_by_project()
MiembroProyectoRepository -> BaseDatos: select_project_members()
Organizador -> GestionIntegrantesPermisos: agregarOModificarPermiso()
GestionIntegrantesPermisos -> ProyectoClient: addMember()
ProyectoClient -> ProyectosController: add_member()
ProyectosController -> ProyectoService: add_member()
ProyectoService -> MiembroProyectoRepository: get_membership()
MiembroProyectoRepository --> ProyectoService: MiembroProyectoOrNull
alt [usuario ya es integrante]
ProyectoService --> ProyectosController: MiembroProyecto
ProyectosController --> GestionIntegrantesPermisos: mostrarIntegranteExistente()
end
ProyectoService -> MiembroProyectoRepository: add()
GestionIntegrantesPermisos -> ProyectoClient: updateMember()
GestionIntegrantesPermisos -> ProyectoClient: setPermission()
ProyectoClient -> ProyectosController: set_permission()
ProyectosController -> ProyectoService: set_permission()
ProyectoService -> MiembroProyectoRepository: get_membership()
alt [organizador insuficiente]
MiembroProyectoRepository --> ProyectoService: MiembroOrNull
ProyectoService --> ProyectosController: errorAutorizacion()
ProyectosController --> GestionIntegrantesPermisos: mostrarError()
end
ProyectoService -> BaseDatos: upsert_project_permissions()
ProyectosController --> GestionIntegrantesPermisos: MiembroProyectoResponse
```

## CU10. Gestionar versiones y cambios del proyecto

Marco: `sd CU10 Gestionar versiones y cambios del proyecto`

Lifelines:
```text
Editor
UI::Colaborativo
Cliente::ProyectoClient
Controlador::ProyectosController
Servicio::ProyectoService
Repositorio::ProyectoRepository
DB::BaseDatos
```

### Flujo principal
```text
Editor -> Colaborativo: guardarVersion()
Colaborativo -> Colaborativo: validarSnapshot()
alt [snapshot invalido]
Colaborativo --> Editor: mostrarError()
end
Colaborativo -> ProyectoClient: createVersion()
ProyectoClient -> ProyectosController: create_version()
ProyectosController -> ProyectoService: create_version()
ProyectoService -> ProyectoRepository: get()
ProyectoRepository --> ProyectoService: ProjectOrNull
alt [proyecto no encontrado]
ProyectoService --> ProyectosController: errorNoEncontrado()
ProyectosController --> Colaborativo: mostrarError()
end
ProyectoService -> ProyectoRepository: next_version_number()
ProyectoRepository -> BaseDatos: select_next_version_number()
ProyectoService -> ProyectoRepository: add()
ProyectoRepository -> BaseDatos: insert_project_versions()
ProyectoService --> ProyectosController: VersionResponse
ProyectosController --> Colaborativo: version creada
```





