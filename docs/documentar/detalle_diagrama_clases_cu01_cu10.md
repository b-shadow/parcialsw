# Detalle de diagramas de clases CU01-CU10

Se excluye CU07. El nivel es de analisis/diseno segun codigo actual: paginas y servicios frontend, routers, servicios backend, repositorios y entidades ORM.

## CU01. Registrar cuenta de usuario

Marco: `class DCD CU01 Registrar cuenta de usuario`

Clases:
```text
Frontend::RegisterPage
- fullName
- email
- password
+ handleSubmit()

Frontend::authService
+ register(payload)
+ login(payload)

API::AuthRouter
+ register(payload)

Servicio::AuthService
+ register(payload)

Repo::UserRepository
+ get_by_email(email)
+ add(user)

Repo::RoleRepository
+ get_by_name(name)

Entidad::User
- id
- full_name
- email
- password_hash
- is_active

Entidad::Role
- id
- name

Entidad::UserRole
- user_id
- role_id

Entidad::AuditLog
- module
- action
- user_id
```

Relaciones:
```text
RegisterPage -> authService
authService -> AuthRouter
AuthRouter -> AuthService
AuthService -> UserRepository
AuthService -> RoleRepository
AuthService -> AuditService
User 1 -- * UserRole
Role 1 -- * UserRole
```

## CU02. Gestionar autenticacion

Clases:
```text
Frontend::LoginPage
- email
- password
+ handleSubmit()

Frontend::authStore
- token
- user
+ setToken()
+ setUser()

Servicio::AuthService
+ login(payload)

Servicio::JWT
+ create_access_token(user_id)

Entidad::UserSession
- user_id
- token_hash
- expires_at
- revoked_at
```

Relaciones:
```text
LoginPage -> authService
LoginPage -> authStore
AuthService -> UserRepository
AuthService -> JWT
AuthService -> AuditService
User 1 -- * UserSession
```

## CU03. Gestionar perfil propio

Clases:
```text
Frontend::ProfilePage
+ cargarPerfil()
+ guardarCambios()

Frontend::userService
+ list()
+ updateUser(id, payload)

API::UsersRouter
+ list_users()
+ update_user()

Servicio::UserService
+ list_users()
+ update_user(user_id, payload)

Entidad::User
- full_name
- email
- is_active
- last_access_at
```

Relaciones:
```text
ProfilePage -> userService
UsersRouter -> UserService
UserService -> UserRepository
UserService -> AuditService
```

## CU04. Gestionar usuarios y roles globales

Clases:
```text
Frontend::ProjectManagementPage
+ cargarUsuarios()
+ actualizarUsuario()

Frontend::userService
+ list()
+ updateUser()

Servicio::UserService
+ list_users()
+ update_user()

Entidad::User
Entidad::Role
Entidad::UserRole
Entidad::AuditLog
```

Relaciones:
```text
ProjectManagementPage -> userService
UserService -> UserRepository
User -- UserRole
Role -- UserRole
UserService -> AuditService
```

## CU05. Consultar reportes del proyecto

Clases:
```text
Frontend::ReportsPage
+ calcularIndicadores()

Frontend::projectService
+ list()

Frontend::umlService
+ listDiagrams(projectId)

Frontend::generationService
+ transform()
+ springBoot()
+ flutter()

Entidad::Project
Entidad::UmlDiagram
Entidad::UmlTransformation
Entidad::GeneratedBackend
Entidad::GeneratedFrontend
```

Relaciones:
```text
ReportsPage -> projectService
ReportsPage -> umlService
ReportsPage -> generationService
Project 1 -- * UmlDiagram
UmlDiagram 1 -- * UmlTransformation
UmlTransformation 1 -- * GeneratedBackend
UmlTransformation 1 -- * GeneratedFrontend
```

## CU06. Consultar bitacora del proyecto

Clases:
```text
Servicio::AuditService
+ record(module, action, user_id, project_id, metadata)

Repo::AuditRepository
+ add(log)

Entidad::AuditLog
- id
- user_id
- project_id
- module
- action
- metadata_json
- created_at

Entidad::Project
Entidad::User
```

Relaciones:
```text
AuditService -> AuditRepository
AuditLog * -- 1 User
AuditLog * -- 0..1 Project
```

## CU08. Gestionar proyectos de desarrollo

Clases:
```text
Frontend::ProjectsPage
- projectName
- projectDescription
+ createProject()
+ listProjects()

Frontend::projectService
+ create()
+ list()
+ update()
+ delete()

Servicio::ProjectService
+ create_project()
+ list_projects()
+ update_project()
+ archive_project()

Entidad::Project
- name
- description
- status
- owner_user_id

Entidad::ProjectMember
- project_id
- user_id
- role
```

Relaciones:
```text
ProjectsPage -> projectService
ProjectService -> ProjectRepository
ProjectService -> MemberRepository
Project 1 -- * ProjectMember
User 1 -- * ProjectMember
```

## CU09. Gestionar integrantes y permisos del proyecto

Clases:
```text
Frontend::ProjectManagementPage
+ addMember()
+ updateMember()
+ setPermission()

Servicio::ProjectService
+ add_member()
+ update_member()
+ remove_member()
+ set_permission()

Entidad::ProjectMember
- role

Entidad::ProjectPermission
- permission_code
- granted
```

Relaciones:
```text
ProjectManagementPage -> projectService
ProjectService -> MemberRepository
ProjectMember 1 -- * ProjectPermission
Project 1 -- * ProjectMember
User 1 -- * ProjectMember
```

## CU10. Gestionar versiones y cambios del proyecto

Clases:
```text
Frontend::ProjectWorkspacePage
+ createVersion()

Servicio::ProjectService
+ create_version(projectId, payload)

Repo::ProjectRepository
+ next_version_number(projectId)
+ add_version(version)

Entidad::ProjectVersion
- version_number
- label
- description
- snapshot
- created_by_user_id
```

Relaciones:
```text
ProjectWorkspacePage -> projectService
ProjectService -> ProjectRepository
Project 1 -- * ProjectVersion
User 1 -- * ProjectVersion
```

