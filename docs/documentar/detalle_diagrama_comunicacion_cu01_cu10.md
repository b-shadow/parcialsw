# Detalle de diagramas de comunicacion CU01-CU10

Se excluye CU07. En Enterprise Architect ubicar objetos libremente y numerar mensajes sobre cada enlace.

El diagrama de comunicacion representa el mismo comportamiento que el diagrama de secuencia, pero no usa marcos `alt`. Los flujos alternativos se dibujan como mensajes condicionados con guardas, por ejemplo `2 [correoExiste] servicio -> router: errorValidacion()`. Si el diagrama queda muy cargado, puede separarse en otro diagrama de comunicacion del mismo CU.

## CU01. Registrar cuenta de usuario

Objetos:
```text
usuario:Usuario
registro:RegisterPage
auth:authService
router:AuthRouter
servicio:AuthService
usuarios:UserRepository
roles:RoleRepository
auditoria:AuditService
db:PostgreSQL
```

### Flujo principal

Mensajes:
```text
1 usuario -> registro: enviarRegistro()
1.1 registro -> auth: register()
1.2 auth -> router: register()
1.3 router -> servicio: register()
1.4 servicio -> usuarios: get_by_email()
1.5 servicio -> roles: get_by_name()
1.6 servicio -> usuarios: add()
1.7 servicio -> auditoria: record()
```

### Condiciones alternativas: Correo ya registrado / Datos invalidos

Mensajes:
```text
2 [correoExiste] servicio -> usuarios: get_by_email()
2.1 [correoExiste] usuarios -> servicio: User
2.2 [correoExiste] servicio -> router: errorValidacion()
2.3 [correoExiste] router -> registro: mostrarError()
3 [datosInvalidos] registro -> registro: validarFormulario()
3.1 [datosInvalidos] registro -> usuario: mostrarError()
```

## CU02. Gestionar autenticacion

### Flujo principal

Mensajes:
```text
1 usuario -> login: ingresarCredenciales()
1.1 login -> auth: login()
1.2 auth -> router: login()
1.3 router -> servicio: login()
1.4 servicio -> usuarios: get_by_email()
1.5 servicio -> servicio: verify_password()
1.6 servicio -> jwt: create_access_token()
1.7 servicio -> auditoria: record()
```

### Condiciones alternativas: Credenciales invalidas / Usuario inactivo

Mensajes:
```text
2 [credencialesInvalidas] servicio -> usuarios: get_by_email()
2.1 [credencialesInvalidas] usuarios -> servicio: UserOrNull
2.2 [credencialesInvalidas] servicio -> servicio: verify_password()
2.3 [credencialesInvalidas] servicio -> router: errorAutenticacion()
2.4 [credencialesInvalidas] router -> login: mostrarError()
3 [usuarioInactivo] servicio -> router: errorAutenticacion()
3.1 [usuarioInactivo] router -> login: mostrarError()
```

## CU03. Gestionar perfil propio

### Flujo principal

Mensajes:
```text
1 usuario -> perfil: abrir()
1.1 perfil -> auth: me()
2 usuario -> perfil: guardarCambios()
2.1 perfil -> userService: updateUser()
2.2 userService -> UsersRouter: update_user()
2.3 UsersRouter -> UserService: update_user()
2.4 UserService -> UserRepository: get_by_id()
2.5 UserService -> AuditService: record()
```

### Condiciones alternativas: Token invalido / Usuario no encontrado

Mensajes:
```text
3 [tokenInvalido] auth -> perfil: errorAutorizacion()
3.1 [tokenInvalido] perfil -> usuario: redirigirLogin()
4 [usuarioNoExiste] UserService -> UserRepository: get_by_id()
4.1 [usuarioNoExiste] UserRepository -> UserService: UserOrNull
4.2 [usuarioNoExiste] UserService -> perfil: mostrarError()
```

## CU04. Gestionar usuarios y roles globales

### Flujo principal

Mensajes:
```text
1 admin -> gestion: listarUsuarios()
1.1 gestion -> userService: list()
1.2 userService -> UsersRouter: list_users()
1.3 UsersRouter -> UserService: list_users()
2 admin -> gestion: actualizarUsuario()
2.1 gestion -> userService: updateUser()
2.2 userService -> UsersRouter: update_user()
2.3 UsersRouter -> UserService: update_user()
2.4 UserService -> UserRepository: get_by_id()
2.5 UserService -> AuditService: record()
```

### Condiciones alternativas: Sin permisos / Usuario objetivo no existe

Mensajes:
```text
3 [sinPermisos] UsersRouter -> UserService: validarPermisos()
3.1 [sinPermisos] UserService -> gestion: errorAutorizacion()
4 [usuarioObjetivoNoExiste] UserService -> UserRepository: get_by_id()
4.1 [usuarioObjetivoNoExiste] UserRepository -> UserService: UserOrNull
4.2 [usuarioObjetivoNoExiste] UserService -> gestion: mostrarError()
```

## CU05. Consultar reportes del proyecto

### Flujo principal

Mensajes:
```text
1 usuario -> reportes: abrir()
1.1 reportes -> projectService: list()
1.2 reportes -> umlService: listDiagrams()
1.3 reportes -> generationService: consultarResultados()
1.4 reportes -> reportes: calcularIndicadores()
```

### Condiciones alternativas: Sin datos / Sin membresia

Mensajes:
```text
2 [sinDatos] projectService -> ProjectRepository: list_for_user()
2.1 [sinDatos] ProjectRepository -> reportes: listaVacia()
2.2 [sinDatos] reportes -> reportes: mostrarEstadoVacio()
3 [sinMembresia] ProjectService -> MemberRepository: get_membership()
3.1 [sinMembresia] MemberRepository -> ProjectService: MemberOrNull
3.2 [sinMembresia] ProjectService -> reportes: mostrarError()
```

## CU06. Consultar bitacora del proyecto

### Flujo principal

Mensajes:
```text
1 organizador -> reportes: consultarBitacora()
1.1 reportes -> ProjectsRouter: get_project()
1.2 ProjectsRouter -> ProjectService: get_project()
1.3 ProjectService -> MemberRepository: get_membership()
1.4 reportes -> AuditService: list_by_project()
1.5 AuditService -> AuditRepository: list_by_project()
1.6 AuditRepository -> db: select_audit_logs()
```

### Condiciones alternativas: Sin permisos / Bitacora vacia

Mensajes:
```text
2 [sinPermisos] ProjectService -> MemberRepository: get_membership()
2.1 [sinPermisos] MemberRepository -> ProjectService: MemberOrNull
2.2 [sinPermisos] ProjectService -> reportes: mostrarError()
3 [bitacoraVacia] AuditRepository -> db: select_audit_logs()
3.1 [bitacoraVacia] db -> AuditRepository: listaVacia()
3.2 [bitacoraVacia] AuditService -> reportes: mostrarEstadoVacio()
```

## CU08. Gestionar proyectos de desarrollo

### Flujo principal

Mensajes:
```text
1 editor -> proyectos: crearProyecto()
1.1 proyectos -> projectService: create()
1.2 projectService -> ProjectsRouter: create_project()
1.3 ProjectsRouter -> ProjectService: create_project()
1.4 ProjectService -> ProjectRepository: add()
1.5 ProjectService -> MemberRepository: add()
1.6 ProjectService -> AuditService: record()
```

### Condiciones alternativas: Datos invalidos / Error de persistencia

Mensajes:
```text
2 [datosInvalidos] proyectos -> proyectos: validarFormulario()
2.1 [datosInvalidos] proyectos -> editor: mostrarError()
3 [errorPersistencia] ProjectRepository -> db: insert_projects()
3.1 [errorPersistencia] db -> ProjectRepository: errorPersistencia()
3.2 [errorPersistencia] ProjectService -> proyectos: mostrarError()
```

## CU09. Gestionar integrantes y permisos del proyecto

### Flujo principal

Mensajes:
```text
1 organizador -> gestion: listarIntegrantes()
1.1 gestion -> projectService: listMembers()
1.2 projectService -> ProjectsRouter: list_members()
1.3 ProjectsRouter -> ProjectService: list_members()
1.4 ProjectService -> MemberRepository: list_by_project()
2 organizador -> gestion: cambiarPermiso()
2.1 gestion -> projectService: setPermission()
2.2 projectService -> ProjectsRouter: set_permission()
2.3 ProjectsRouter -> ProjectService: set_permission()
2.4 ProjectService -> MemberRepository: get()
2.5 ProjectService -> ProjectPermission: upsert()
```

### Condiciones alternativas: Integrante existente / Organizador insuficiente

Mensajes:
```text
3 [integranteExistente] ProjectService -> MemberRepository: get_membership()
3.1 [integranteExistente] MemberRepository -> ProjectService: ProjectMember
3.2 [integranteExistente] ProjectService -> gestion: mostrarIntegranteExistente()
4 [organizadorInsuficiente] ProjectService -> MemberRepository: get_membership()
4.1 [organizadorInsuficiente] MemberRepository -> ProjectService: MemberOrNull
4.2 [organizadorInsuficiente] ProjectService -> gestion: mostrarError()
```

## CU10. Gestionar versiones y cambios del proyecto

### Flujo principal

Mensajes:
```text
1 editor -> colaborativo: guardarVersion()
1.1 colaborativo -> projectService: createVersion()
1.2 projectService -> ProjectsRouter: create_version()
1.3 ProjectsRouter -> ProjectService: create_version()
1.4 ProjectService -> ProjectRepository: next_version_number()
1.5 ProjectService -> ProjectRepository: add()
```

### Condiciones alternativas: Proyecto no encontrado / Snapshot invalido

Mensajes:
```text
2 [proyectoNoExiste] ProjectService -> ProjectRepository: get()
2.1 [proyectoNoExiste] ProjectRepository -> ProjectService: ProjectOrNull
2.2 [proyectoNoExiste] ProjectService -> colaborativo: mostrarError()
3 [snapshotInvalido] colaborativo -> colaborativo: validarSnapshot()
3.1 [snapshotInvalido] colaborativo -> editor: mostrarError()
```
