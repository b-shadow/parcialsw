# Detalle de diagramas de secuencia CU01-CU10

Se excluye CU07. Estilo: actor a la izquierda, frontend, API, servicio, repositorio y base de datos. Usar flecha continua para llamadas y punteada para retornos.

Los fragmentos `alt [condicion] ... end` estan integrados en el flujo principal. En Enterprise Architect se dibujan como Combined Fragment con operador `alt` exactamente en esa posicion; al cerrar `end`, el flujo continua con la siguiente linea.

## CU01. Registrar cuenta de usuario

Marco: `sd CU01 Registrar cuenta de usuario`

Lifelines:
```text
Usuario
Frontend::RegisterPage
Frontend::authService
API::AuthRouter
Servicio::AuthService
Repo::UserRepository
Repo::RoleRepository
Servicio::AuditService
DB::PostgreSQL
```

### Flujo principal
```text
Usuario -> RegisterPage: enviarRegistro()
RegisterPage -> RegisterPage: validarFormulario()
alt [datos invalidos]
RegisterPage --> Usuario: mostrarError()
end
RegisterPage -> authService: register()
authService -> AuthRouter: register()
AuthRouter -> AuthService: register()
AuthService -> UserRepository: get_by_email()
UserRepository -> PostgreSQL: select_users()
PostgreSQL --> UserRepository: UserOrNull
alt [correo ya registrado]
AuthService --> AuthRouter: errorValidacion()
AuthRouter --> RegisterPage: mostrarError()
end
AuthService -> AuthService: hash_password()
AuthService -> RoleRepository: get_by_name()
RoleRepository -> PostgreSQL: select_roles()
AuthService -> UserRepository: add()
UserRepository -> PostgreSQL: insert_users()
AuthService -> AuditService: record()
AuditService -> PostgreSQL: insert_audit_logs()
AuthService --> AuthRouter: User
AuthRouter --> authService: UserResponse
authService --> RegisterPage: usuario registrado
```

## CU02. Gestionar autenticacion

Marco: `sd CU02 Gestionar autenticacion`

Lifelines:
```text
Usuario
Frontend::LoginPage
Frontend::authService
API::AuthRouter
Servicio::AuthService
Repo::UserRepository
Servicio::JWT
Servicio::AuditService
DB::PostgreSQL
```

### Flujo principal
```text
Usuario -> LoginPage: ingresarCredenciales()
LoginPage -> authService: login()
authService -> AuthRouter: login()
AuthRouter -> AuthService: login()
AuthService -> UserRepository: get_by_email()
UserRepository -> PostgreSQL: select_users()
PostgreSQL --> UserRepository: UserOrNull
AuthService -> AuthService: verify_password()
alt [credenciales invalidas]
AuthService --> AuthRouter: errorAutenticacion()
AuthRouter --> LoginPage: mostrarError()
end
alt [usuario inactivo]
AuthService --> AuthRouter: errorAutenticacion()
AuthRouter --> LoginPage: mostrarError()
end
AuthService -> JWT: create_access_token()
JWT --> AuthService: token
AuthService -> AuditService: record()
AuditService -> PostgreSQL: insert_audit_logs()
AuthService --> AuthRouter: TokenResponse
AuthRouter --> authService: JWT
authService --> LoginPage: access_token
LoginPage -> LoginPage: guardarSesion()
```

## CU03. Gestionar perfil propio

Marco: `sd CU03 Gestionar perfil propio`

Lifelines:
```text
Usuario
Frontend::ProfilePage
Frontend::userService
API::AuthRouter
API::UsersRouter
Servicio::UserService
Repo::UserRepository
Servicio::AuditService
DB::PostgreSQL
```

### Flujo principal
```text
Usuario -> ProfilePage: abrirPerfil()
ProfilePage -> userService: me()
userService -> AuthRouter: me()
alt [token invalido o sesion expirada]
AuthRouter --> userService: errorAutorizacion()
userService --> ProfilePage: redirigirLogin()
end
AuthRouter --> userService: UserResponse
Usuario -> ProfilePage: actualizarDatos()
ProfilePage -> userService: updateUser()
userService -> UsersRouter: update_user()
UsersRouter -> UserService: update_user()
UserService -> UserRepository: get_by_id()
UserRepository -> PostgreSQL: select_users()
UserRepository --> UserService: UserOrNull
alt [usuario no encontrado]
UserService --> UsersRouter: errorNoEncontrado()
UsersRouter --> ProfilePage: mostrarError()
end
UserService -> UserRepository: update()
UserRepository -> PostgreSQL: update_users()
UserService -> AuditService: record()
AuditService -> PostgreSQL: insert_audit_logs()
UserService --> UsersRouter: User
UsersRouter --> ProfilePage: UserResponse
```

## CU04. Gestionar usuarios y roles globales

Marco: `sd CU04 Gestionar usuarios y roles globales`

Lifelines:
```text
Administrador
Frontend::ProjectManagementPage
Frontend::userService
API::UsersRouter
Servicio::UserService
Repo::UserRepository
Servicio::AuditService
DB::PostgreSQL
```

### Flujo principal
```text
Administrador -> ProjectManagementPage: consultarUsuarios()
ProjectManagementPage -> userService: list()
userService -> UsersRouter: list_users()
UsersRouter -> UserService: list_users()
UserService -> UserRepository: list()
UserRepository -> PostgreSQL: select_users()
PostgreSQL --> UserRepository: List<User>
UsersRouter --> ProjectManagementPage: List<UserResponse>
Administrador -> ProjectManagementPage: cambiarEstado()
ProjectManagementPage -> userService: updateUser()
userService -> UsersRouter: update_user()
UsersRouter -> UserService: validarPermisos()
alt [sin permisos de administracion]
UserService --> UsersRouter: errorAutorizacion()
UsersRouter --> ProjectManagementPage: mostrarError()
end
UsersRouter -> UserService: update_user()
UserService -> UserRepository: get_by_id()
UserRepository --> UserService: UserOrNull
alt [usuario objetivo no existe]
UserService --> UsersRouter: errorNoEncontrado()
UsersRouter --> ProjectManagementPage: mostrarError()
end
UserService -> PostgreSQL: update_users()
UserService -> AuditService: record()
AuditService -> PostgreSQL: insert_audit_logs()
```

## CU05. Consultar reportes del proyecto

Marco: `sd CU05 Consultar reportes del proyecto`

Lifelines:
```text
Usuario
Frontend::ReportsPage
Frontend::projectService
Frontend::umlService
Frontend::generationService
API::ProjectsRouter
API::UmlRouter
API::GenerationRouter
Servicio::ProjectService
Repo::ProjectRepository
Repo::MemberRepository
Servicio::UmlService
Repo::UmlRepository
Repo::GenerationRepository
DB::PostgreSQL
```

### Flujo principal
```text
Usuario -> ReportsPage: abrirReportes()
ReportsPage -> projectService: list()
projectService -> ProjectsRouter: list_projects()
ProjectsRouter -> ProjectService: list_projects()
ProjectService -> MemberRepository: get_membership()
alt [sin membresia del proyecto]
ProjectService --> ProjectsRouter: errorAutorizacion()
ProjectsRouter --> ReportsPage: mostrarError()
end
ProjectService -> ProjectRepository: list_for_user()
ProjectRepository -> PostgreSQL: select_projects()
ProjectRepository --> ProjectService: List<Project>
ReportsPage -> umlService: listDiagrams()
umlService -> UmlRouter: list_diagrams()
UmlRouter -> UmlService: list_diagrams()
UmlService -> UmlRepository: list_diagrams_by_project()
UmlRepository -> PostgreSQL: select_uml_diagrams()
UmlRepository --> UmlService: List<UmlDiagram>
alt [proyecto sin datos disponibles]
ReportsPage -> ReportsPage: mostrarEstadoVacio()
end
ReportsPage -> generationService: consultarResultados()
generationService -> GenerationRepository: get_transformation()
GenerationRepository -> PostgreSQL: select_transformations()
ReportsPage -> ReportsPage: calcularIndicadores()
```

## CU06. Consultar bitacora del proyecto

Marco: `sd CU06 Consultar bitacora del proyecto`

Lifelines:
```text
Organizador
Frontend::ReportsPage
API::ProjectsRouter
Servicio::ProjectService
Repo::MemberRepository
Servicio::AuditService
Repo::AuditRepository
DB::PostgreSQL
```

### Flujo principal
```text
Organizador -> ReportsPage: consultarActividad()
ReportsPage -> ProjectsRouter: get_project()
ProjectsRouter -> ProjectService: get_project()
ProjectService -> MemberRepository: get_membership()
MemberRepository -> PostgreSQL: select_project_members()
MemberRepository --> ProjectService: MemberOrNull
alt [sin permisos para consultar bitacora]
ProjectService --> ProjectsRouter: errorAutorizacion()
ProjectsRouter --> ReportsPage: mostrarError()
end
ReportsPage -> AuditService: consultarBitacora()
AuditService -> AuditRepository: list_by_project()
AuditRepository -> PostgreSQL: select_audit_logs()
PostgreSQL --> AuditRepository: List<AuditLog>
alt [bitacora vacia]
AuditService --> ReportsPage: mostrarEstadoVacio()
end
AuditService --> ReportsPage: acciones, usuario, fecha, modulo
```

## CU08. Gestionar proyectos de desarrollo

Marco: `sd CU08 Gestionar proyectos de desarrollo`

Lifelines:
```text
Editor
Frontend::ProjectsPage
Frontend::projectService
API::ProjectsRouter
Servicio::ProjectService
Repo::ProjectRepository
Repo::MemberRepository
Servicio::AuditService
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> ProjectsPage: crearProyecto()
ProjectsPage -> ProjectsPage: validarFormulario()
alt [nombre o datos invalidos]
ProjectsPage --> Editor: mostrarError()
end
ProjectsPage -> projectService: create()
projectService -> ProjectsRouter: create_project()
ProjectsRouter -> ProjectService: create_project()
ProjectService -> ProjectRepository: add()
ProjectRepository -> PostgreSQL: insert_projects()
alt [error al persistir proyecto]
PostgreSQL --> ProjectRepository: errorPersistencia()
ProjectService --> ProjectsRouter: errorPersistencia()
ProjectsRouter --> ProjectsPage: mostrarError()
end
ProjectService -> MemberRepository: add()
MemberRepository -> PostgreSQL: insert_project_members()
ProjectService -> AuditService: record()
AuditService -> PostgreSQL: insert_audit_logs()
ProjectService --> ProjectsRouter: Project
ProjectsRouter --> ProjectsPage: ProjectResponse
```

## CU09. Gestionar integrantes y permisos del proyecto

Marco: `sd CU09 Gestionar integrantes y permisos del proyecto`

Lifelines:
```text
Organizador
Frontend::ProjectManagementPage
Frontend::projectService
API::ProjectsRouter
Servicio::ProjectService
Repo::MemberRepository
DB::PostgreSQL
```

### Flujo principal
```text
Organizador -> ProjectManagementPage: abrirIntegrantes()
ProjectManagementPage -> projectService: listMembers()
projectService -> ProjectsRouter: list_members()
ProjectsRouter -> ProjectService: list_members()
ProjectService -> MemberRepository: list_by_project()
MemberRepository -> PostgreSQL: select_project_members()
Organizador -> ProjectManagementPage: agregarOModificarPermiso()
ProjectManagementPage -> projectService: addMember()
projectService -> ProjectsRouter: add_member()
ProjectsRouter -> ProjectService: add_member()
ProjectService -> MemberRepository: get_membership()
MemberRepository --> ProjectService: ProjectMemberOrNull
alt [usuario ya es integrante]
ProjectService --> ProjectsRouter: ProjectMember
ProjectsRouter --> ProjectManagementPage: mostrarIntegranteExistente()
end
ProjectService -> MemberRepository: add()
ProjectManagementPage -> projectService: updateMember()
ProjectManagementPage -> projectService: setPermission()
projectService -> ProjectsRouter: set_permission()
ProjectsRouter -> ProjectService: set_permission()
ProjectService -> MemberRepository: get_membership()
alt [organizador insuficiente]
MemberRepository --> ProjectService: MemberOrNull
ProjectService --> ProjectsRouter: errorAutorizacion()
ProjectsRouter --> ProjectManagementPage: mostrarError()
end
ProjectService -> PostgreSQL: upsert_project_permissions()
ProjectsRouter --> ProjectManagementPage: ProjectMemberResponse
```

## CU10. Gestionar versiones y cambios del proyecto

Marco: `sd CU10 Gestionar versiones y cambios del proyecto`

Lifelines:
```text
Editor
Frontend::ProjectWorkspacePage
Frontend::projectService
API::ProjectsRouter
Servicio::ProjectService
Repo::ProjectRepository
DB::PostgreSQL
```

### Flujo principal
```text
Editor -> ProjectWorkspacePage: guardarVersion()
ProjectWorkspacePage -> ProjectWorkspacePage: validarSnapshot()
alt [snapshot invalido]
ProjectWorkspacePage --> Editor: mostrarError()
end
ProjectWorkspacePage -> projectService: createVersion()
projectService -> ProjectsRouter: create_version()
ProjectsRouter -> ProjectService: create_version()
ProjectService -> ProjectRepository: get()
ProjectRepository --> ProjectService: ProjectOrNull
alt [proyecto no encontrado]
ProjectService --> ProjectsRouter: errorNoEncontrado()
ProjectsRouter --> ProjectWorkspacePage: mostrarError()
end
ProjectService -> ProjectRepository: next_version_number()
ProjectRepository -> PostgreSQL: select_next_version_number()
ProjectService -> ProjectRepository: add()
ProjectRepository -> PostgreSQL: insert_project_versions()
ProjectService --> ProjectsRouter: VersionResponse
ProjectsRouter --> ProjectWorkspacePage: version creada
```
