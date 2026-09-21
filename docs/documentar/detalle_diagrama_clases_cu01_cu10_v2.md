# Detalle de diagramas de clases CU01-CU10 v2

Se excluye CU07. Version v2: usa nombres semanticos para diagramar. Un diagrama de clases UML debe mostrar clases, atributos, operaciones y relaciones estructurales; por eso las entidades persistentes incluyen atributos del modelo y las capas de UI/cliente/controlador/servicio/repositorio incluyen operaciones relevantes.

## CU01. Registrar cuenta de usuario

Marco: `class DCD CU01 Registrar cuenta de usuario`

Clases:
```text
UI::RegistroUsuario
- fullName
- email
- password
+ validarFormulario()
+ enviarRegistro()
+ mostrarError()

Cliente::AutenticacionClient
+ register(payload)

Controlador::AutenticacionController
+ register(payload)

Servicio::AutenticacionService
+ register(payload)
- hash_password(password)

Repositorio::UsuarioRepository
+ get_by_email(email)
+ add(user)

Repositorio::RolRepository
+ get_by_name(name)

Servicio::AuditoriaService
+ record(module, action, user_id, project_id, metadata)

Entidad::Usuario
- id
- full_name
- email
- password_hash
- is_active
- last_access_at
- created_at
- updated_at

Entidad::Rol
- id
- name
- description
- is_system

Entidad::UsuarioRol
- id
- user_id
- role_id

Entidad::Auditoria
- id
- user_id
- project_id
- module
- action
- result
- detail
- metadata_json
- created_at
```

Relaciones:
```text
RegistroUsuario -> AutenticacionClient
AutenticacionClient -> AutenticacionController
AutenticacionController -> AutenticacionService
AutenticacionService -> UsuarioRepository
AutenticacionService -> RolRepository
AutenticacionService -> AuditoriaService
Usuario 1 -- * UsuarioRol
Rol 1 -- * UsuarioRol
Usuario 0..1 -- * Auditoria
```

## CU02. Gestionar autenticacion

Marco: `class DCD CU02 Gestionar autenticacion`

Clases:
```text
UI::Login
- email
- password
- rememberMe
+ validarFormulario()
+ enviarCredenciales()
+ guardarSesion()
+ mostrarError()

Cliente::AutenticacionClient
+ login(payload)
+ me()

Cliente::SesionStore
- token
- user
+ setToken(token)
+ setUser(user)
+ clear()

Controlador::AutenticacionController
+ login(payload)
+ me(current_user)

Servicio::AutenticacionService
+ login(payload)
- verify_password(password, hash)
- create_access_token(user_id)

Repositorio::UsuarioRepository
+ get_by_email(email)

Servicio::AuditoriaService
+ record(module, action, user_id, project_id, metadata)

Entidad::Usuario
- id
- email
- password_hash
- is_active
- last_access_at

Entidad::SesionUsuario
- id
- user_id
- refresh_token_hash
- ip_address
- user_agent
- revoked_at
- expires_at
- created_at
```

Relaciones:
```text
Login -> AutenticacionClient
Login -> SesionStore
AutenticacionController -> AutenticacionService
AutenticacionService -> UsuarioRepository
AutenticacionService -> AuditoriaService
Usuario 1 -- * SesionUsuario
```

## CU03. Gestionar perfil propio

Marco: `class DCD CU03 Gestionar perfil propio`

Clases:
```text
UI::PerfilUsuario
- fullName
- email
+ cargarPerfil()
+ guardarCambios()
+ mostrarError()

Cliente::UsuarioClient
+ me()
+ updateUser(id, payload)

Controlador::AutenticacionController
+ me(current_user)

Controlador::UsuariosController
+ update_user(user_id, payload)

Servicio::UsuarioService
+ update_user(user_id, payload)
+ list_users()

Repositorio::UsuarioRepository
+ get_by_id(user_id)
+ update(user)

Servicio::AuditoriaService
+ record(module, action, user_id, project_id, metadata)

Entidad::Usuario
- id
- full_name
- email
- is_active
- last_access_at
- updated_at
```

Relaciones:
```text
PerfilUsuario -> UsuarioClient
UsuarioClient -> AutenticacionController
UsuarioClient -> UsuariosController
UsuariosController -> UsuarioService
UsuarioService -> UsuarioRepository
UsuarioService -> AuditoriaService
```

## CU04. Gestionar usuarios y roles globales

Marco: `class DCD CU04 Gestionar usuarios y roles globales`

Clases:
```text
UI::GestionUsuarios
- users
- selectedUser
+ cargarUsuarios()
+ actualizarUsuario()
+ mostrarError()

Cliente::UsuarioClient
+ list()
+ updateUser(id, payload)

Controlador::UsuariosController
+ list_users()
+ update_user(user_id, payload)

Servicio::UsuarioService
+ list_users()
+ update_user(user_id, payload)
- validarPermisos(current_user)

Repositorio::UsuarioRepository
+ list()
+ get_by_id(user_id)
+ update(user)

Entidad::Usuario
- id
- full_name
- email
- is_active
- last_access_at

Entidad::Rol
- id
- name
- description
- is_system

Entidad::UsuarioRol
- id
- user_id
- role_id

Entidad::Auditoria
- id
- user_id
- module
- action
- result
- metadata_json
```

Relaciones:
```text
GestionUsuarios -> UsuarioClient
UsuarioClient -> UsuariosController
UsuariosController -> UsuarioService
UsuarioService -> UsuarioRepository
UsuarioService -> AuditoriaService
Usuario 1 -- * UsuarioRol
Rol 1 -- * UsuarioRol
Usuario 0..1 -- * Auditoria
```

## CU05. Consultar reportes del proyecto

Marco: `class DCD CU05 Consultar reportes del proyecto`

Clases:
```text
UI::Reportes
- indicadores
- filtros
+ cargarProyectos()
+ cargarDiagramas()
+ cargarGeneraciones()
+ calcularIndicadores()
+ mostrarEstadoVacio()

Cliente::ProyectoClient
+ list()
+ getProject(projectId)

Cliente::ModeladoUMLClient
+ listDiagrams(projectId)

Cliente::GeneracionClient
+ transform(payload)
+ springBoot(payload)
+ flutter(payload)

Servicio::ProyectoService
+ list_projects(user)
+ get_project(project_id, user)

Servicio::ModeladoUMLService
+ list_diagrams(project_id, user)

Servicio::GeneracionService
+ get_transformation(transformation_id, user)

Repositorio::ProyectoRepository
+ list_for_user(user_id)

Repositorio::ModeloUMLRepository
+ list_diagrams_by_project(project_id)

Repositorio::GeneracionRepository
+ get_transformation(transformation_id)

Entidad::Proyecto
- id
- owner_id
- name
- description
- status
- settings
- created_at
- updated_at

Entidad::DiagramaUML
- id
- project_id
- created_by_user_id
- name
- diagram_type
- status
- current_version
- description
- metadata_json

Entidad::TransformacionUML
- id
- project_id
- diagram_id
- requested_by_user_id
- source_version
- target_platform
- intermediate_model
- status
- error_detail

Entidad::BackendGenerado
- id
- project_id
- transformation_id
- generated_by_user_id
- name
- technology
- language
- database_engine
- version_label
- status
- artifact_path
- manifest

Entidad::FrontendGenerado
- id
- project_id
- transformation_id
- generated_by_user_id
- backend_id
- name
- technology
- language
- version_label
- status
- artifact_path
- manifest
```

Relaciones:
```text
Reportes -> ProyectoClient
Reportes -> ModeladoUMLClient
Reportes -> GeneracionClient
ProyectoClient -> ProyectoService
ModeladoUMLClient -> ModeladoUMLService
GeneracionClient -> GeneracionService
ProyectoService -> ProyectoRepository
ModeladoUMLService -> ModeloUMLRepository
GeneracionService -> GeneracionRepository
Proyecto 1 -- * DiagramaUML
Proyecto 1 -- * TransformacionUML
DiagramaUML 1 -- * TransformacionUML
TransformacionUML 1 -- * BackendGenerado
TransformacionUML 1 -- * FrontendGenerado
BackendGenerado 0..1 -- * FrontendGenerado
```

## CU06. Consultar bitacora del proyecto

Marco: `class DCD CU06 Consultar bitacora del proyecto`

Clases:
```text
UI::Reportes
+ consultarBitacora()
+ mostrarEventos()
+ mostrarEstadoVacio()

Servicio::ProyectoService
+ get_project(project_id, user)
- verificarMembresia(project_id, user_id)

Servicio::AuditoriaService
+ record(module, action, user_id, project_id, metadata)
+ list_by_project(project_id)

Repositorio::AuditoriaRepository
+ add(log)
+ list_by_project(project_id)

Repositorio::MiembroProyectoRepository
+ get_membership(project_id, user_id)

Entidad::Auditoria
- id
- user_id
- project_id
- module
- action
- result
- detail
- metadata_json
- created_at

Entidad::Proyecto
- id
- name
- status

Entidad::Usuario
- id
- full_name
- email
```

Relaciones:
```text
Reportes -> ProyectoService
Reportes -> AuditoriaService
ProyectoService -> MiembroProyectoRepository
AuditoriaService -> AuditoriaRepository
Auditoria * -- 0..1 Usuario
Auditoria * -- 0..1 Proyecto
```

## CU08. Gestionar proyectos de desarrollo

Marco: `class DCD CU08 Gestionar proyectos de desarrollo`

Clases:
```text
UI::Proyectos
- projectName
- projectDescription
- projects
+ createProject()
+ listProjects()
+ updateProject()
+ deleteProject()

Cliente::ProyectoClient
+ create(payload)
+ list()
+ update(projectId, payload)
+ delete(projectId)

Controlador::ProyectosController
+ create_project(payload)
+ list_projects()
+ update_project(project_id, payload)
+ archive_project(project_id)

Servicio::ProyectoService
+ create_project(payload, user)
+ list_projects(user)
+ update_project(project_id, payload, user)
+ archive_project(project_id, user)

Repositorio::ProyectoRepository
+ add(project)
+ list_for_user(user_id)
+ get_by_id(project_id)
+ update(project)

Repositorio::MiembroProyectoRepository
+ add(member)
+ get_membership(project_id, user_id)

Entidad::Proyecto
- id
- owner_id
- name
- description
- status
- settings
- created_at
- updated_at

Entidad::MiembroProyecto
- id
- project_id
- user_id
- project_role
- joined_at
```

Relaciones:
```text
Proyectos -> ProyectoClient
ProyectoClient -> ProyectosController
ProyectosController -> ProyectoService
ProyectoService -> ProyectoRepository
ProyectoService -> MiembroProyectoRepository
Proyecto 1 -- * MiembroProyecto
Usuario 1 -- * MiembroProyecto
```

## CU09. Gestionar integrantes y permisos del proyecto

Marco: `class DCD CU09 Gestionar integrantes y permisos del proyecto`

Clases:
```text
UI::GestionIntegrantesPermisos
- members
- permissions
+ listMembers()
+ addMember()
+ updateMember()
+ setPermission()
+ removeMember()

Cliente::ProyectoClient
+ listMembers(projectId)
+ addMember(projectId, payload)
+ updateMember(projectId, memberId, payload)
+ setPermission(projectId, memberId, payload)
+ removeMember(projectId, memberId)

Controlador::ProyectosController
+ list_members(project_id)
+ add_member(project_id, payload)
+ update_member(project_id, member_id, payload)
+ set_permission(project_id, member_id, payload)
+ remove_member(project_id, member_id)

Servicio::ProyectoService
+ list_members(project_id, user)
+ add_member(project_id, payload, user)
+ update_member(project_id, member_id, payload, user)
+ set_permission(project_id, member_id, payload, user)
+ remove_member(project_id, member_id, user)

Repositorio::MiembroProyectoRepository
+ list_by_project(project_id)
+ get_membership(project_id, user_id)
+ add(member)
+ update(member)
+ delete(member)

Entidad::MiembroProyecto
- id
- project_id
- user_id
- project_role
- joined_at

Entidad::PermisoProyecto
- id
- member_id
- permission_code
- is_allowed
```

Relaciones:
```text
GestionIntegrantesPermisos -> ProyectoClient
ProyectoClient -> ProyectosController
ProyectosController -> ProyectoService
ProyectoService -> MiembroProyectoRepository
MiembroProyecto 1 -- * PermisoProyecto
Proyecto 1 -- * MiembroProyecto
Usuario 1 -- * MiembroProyecto
```

## CU10. Gestionar versiones y cambios del proyecto

Marco: `class DCD CU10 Gestionar versiones y cambios del proyecto`

Clases:
```text
UI::Colaborativo
- projectId
- currentDiagram
+ createVersion()
+ mostrarVersionCreada()
+ mostrarError()

Cliente::ProyectoClient
+ createVersion(projectId, payload)

Controlador::ProyectosController
+ create_version(project_id, payload)

Servicio::ProyectoService
+ create_version(project_id, payload, user)

Repositorio::ProyectoRepository
+ get_by_id(project_id)
+ next_version_number(project_id)
+ add_version(version)

Entidad::VersionProyecto
- id
- project_id
- created_by_user_id
- version_number
- name
- description
- snapshot
- status
- created_at

Entidad::Proyecto
- id
- name
- status
```

Relaciones:
```text
Colaborativo -> ProyectoClient
ProyectoClient -> ProyectosController
ProyectosController -> ProyectoService
ProyectoService -> ProyectoRepository
Proyecto 1 -- * VersionProyecto
Usuario 1 -- * VersionProyecto
```

