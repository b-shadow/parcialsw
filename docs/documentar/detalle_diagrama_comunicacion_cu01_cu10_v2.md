# Detalle de diagramas de comunicacion CU01-CU10

Se excluye CU07. En Enterprise Architect ubicar objetos libremente y numerar mensajes sobre cada enlace.

El diagrama de comunicacion representa el mismo comportamiento que el diagrama de secuencia, pero no usa marcos `alt`. Los flujos alternativos se dibujan como mensajes condicionados con guardas, por ejemplo `2 [correoExiste] servicio -> router: errorValidacion()`. Si el diagrama queda muy cargado, puede separarse en otro diagrama de comunicacion del mismo CU.

## CU01. Registrar cuenta de usuario

Objetos:
```text
usuario:Usuario
registro:RegistroUsuario
auth:AutenticacionClient
router:AutenticacionController
servicio:AutenticacionService
usuarios:UsuarioRepository
roles:RolRepository
auditoria:AuditoriaService
db:BaseDatos
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
2.1 [correoExiste] usuarios -> servicio: Usuario
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
1.6 servicio -> token: create_access_token()
1.7 servicio -> auditoria: record()
```

### Condiciones alternativas: Credenciales invalidas / Usuario inactivo

Mensajes:
```text
2 [credencialesInvalidas] servicio -> usuarios: get_by_email()
2.1 [credencialesInvalidas] usuarios -> servicio: UsuarioOrNull
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
2.1 perfil -> UsuarioClient: updateUser()
2.2 UsuarioClient -> UsuariosController: update_user()
2.3 UsuariosController -> UsuarioService: update_user()
2.4 UsuarioService -> UsuarioRepository: get_by_id()
2.5 UsuarioService -> AuditoriaService: record()
```

### Condiciones alternativas: Token invalido / Usuario no encontrado

Mensajes:
```text
3 [tokenInvalido] auth -> perfil: errorAutorizacion()
3.1 [tokenInvalido] perfil -> usuario: redirigirLogin()
4 [usuarioNoExiste] UsuarioService -> UsuarioRepository: get_by_id()
4.1 [usuarioNoExiste] UsuarioRepository -> UsuarioService: UsuarioOrNull
4.2 [usuarioNoExiste] UsuarioService -> perfil: mostrarError()
```

## CU04. Gestionar usuarios y roles globales

### Flujo principal

Mensajes:
```text
1 admin -> gestion: listarUsuarios()
1.1 gestion -> UsuarioClient: list()
1.2 UsuarioClient -> UsuariosController: list_users()
1.3 UsuariosController -> UsuarioService: list_users()
2 admin -> gestion: actualizarUsuario()
2.1 gestion -> UsuarioClient: updateUser()
2.2 UsuarioClient -> UsuariosController: update_user()
2.3 UsuariosController -> UsuarioService: update_user()
2.4 UsuarioService -> UsuarioRepository: get_by_id()
2.5 UsuarioService -> AuditoriaService: record()
```

### Condiciones alternativas: Sin permisos / Usuario objetivo no existe

Mensajes:
```text
3 [sinPermisos] UsuariosController -> UsuarioService: validarPermisos()
3.1 [sinPermisos] UsuarioService -> gestion: errorAutorizacion()
4 [usuarioObjetivoNoExiste] UsuarioService -> UsuarioRepository: get_by_id()
4.1 [usuarioObjetivoNoExiste] UsuarioRepository -> UsuarioService: UsuarioOrNull
4.2 [usuarioObjetivoNoExiste] UsuarioService -> gestion: mostrarError()
```

## CU05. Consultar reportes del proyecto

### Flujo principal

Mensajes:
```text
1 usuario -> reportes: abrir()
1.1 reportes -> ProyectoClient: list()
1.2 reportes -> ModeladoUMLClient: listDiagrams()
1.3 reportes -> GeneracionClient: consultarResultados()
1.4 reportes -> reportes: calcularIndicadores()
```

### Condiciones alternativas: Sin datos / Sin membresia

Mensajes:
```text
2 [sinDatos] ProyectoClient -> ProyectoRepository: list_for_user()
2.1 [sinDatos] ProyectoRepository -> reportes: listaVacia()
2.2 [sinDatos] reportes -> reportes: mostrarEstadoVacio()
3 [sinMembresia] ProyectoService -> MiembroProyectoRepository: get_membership()
3.1 [sinMembresia] MiembroProyectoRepository -> ProyectoService: MiembroOrNull
3.2 [sinMembresia] ProyectoService -> reportes: mostrarError()
```

## CU06. Consultar bitacora del proyecto

### Flujo principal

Mensajes:
```text
1 organizador -> reportes: consultarBitacora()
1.1 reportes -> ProyectosController: get_project()
1.2 ProyectosController -> ProyectoService: get_project()
1.3 ProyectoService -> MiembroProyectoRepository: get_membership()
1.4 reportes -> AuditoriaService: list_by_project()
1.5 AuditoriaService -> AuditoriaRepository: list_by_project()
1.6 AuditoriaRepository -> db: select_audit_logs()
```

### Condiciones alternativas: Sin permisos / Bitacora vacia

Mensajes:
```text
2 [sinPermisos] ProyectoService -> MiembroProyectoRepository: get_membership()
2.1 [sinPermisos] MiembroProyectoRepository -> ProyectoService: MiembroOrNull
2.2 [sinPermisos] ProyectoService -> reportes: mostrarError()
3 [bitacoraVacia] AuditoriaRepository -> db: select_audit_logs()
3.1 [bitacoraVacia] db -> AuditoriaRepository: listaVacia()
3.2 [bitacoraVacia] AuditoriaService -> reportes: mostrarEstadoVacio()
```

## CU08. Gestionar proyectos de desarrollo

### Flujo principal

Mensajes:
```text
1 editor -> proyectos: crearProyecto()
1.1 proyectos -> ProyectoClient: create()
1.2 ProyectoClient -> ProyectosController: create_project()
1.3 ProyectosController -> ProyectoService: create_project()
1.4 ProyectoService -> ProyectoRepository: add()
1.5 ProyectoService -> MiembroProyectoRepository: add()
1.6 ProyectoService -> AuditoriaService: record()
```

### Condiciones alternativas: Datos invalidos / Error de persistencia

Mensajes:
```text
2 [datosInvalidos] proyectos -> proyectos: validarFormulario()
2.1 [datosInvalidos] proyectos -> editor: mostrarError()
3 [errorPersistencia] ProyectoRepository -> db: insert_projects()
3.1 [errorPersistencia] db -> ProyectoRepository: errorPersistencia()
3.2 [errorPersistencia] ProyectoService -> proyectos: mostrarError()
```

## CU09. Gestionar integrantes y permisos del proyecto

### Flujo principal

Mensajes:
```text
1 organizador -> gestion: listarIntegrantes()
1.1 gestion -> ProyectoClient: listMembers()
1.2 ProyectoClient -> ProyectosController: list_members()
1.3 ProyectosController -> ProyectoService: list_members()
1.4 ProyectoService -> MiembroProyectoRepository: list_by_project()
2 organizador -> gestion: cambiarPermiso()
2.1 gestion -> ProyectoClient: setPermission()
2.2 ProyectoClient -> ProyectosController: set_permission()
2.3 ProyectosController -> ProyectoService: set_permission()
2.4 ProyectoService -> MiembroProyectoRepository: get()
2.5 ProyectoService -> PermisoProyecto: upsert()
```

### Condiciones alternativas: Integrante existente / Organizador insuficiente

Mensajes:
```text
3 [integranteExistente] ProyectoService -> MiembroProyectoRepository: get_membership()
3.1 [integranteExistente] MiembroProyectoRepository -> ProyectoService: MiembroProyecto
3.2 [integranteExistente] ProyectoService -> gestion: mostrarIntegranteExistente()
4 [organizadorInsuficiente] ProyectoService -> MiembroProyectoRepository: get_membership()
4.1 [organizadorInsuficiente] MiembroProyectoRepository -> ProyectoService: MiembroOrNull
4.2 [organizadorInsuficiente] ProyectoService -> gestion: mostrarError()
```

## CU10. Gestionar versiones y cambios del proyecto

### Flujo principal

Mensajes:
```text
1 editor -> colaborativo: guardarVersion()
1.1 colaborativo -> ProyectoClient: createVersion()
1.2 ProyectoClient -> ProyectosController: create_version()
1.3 ProyectosController -> ProyectoService: create_version()
1.4 ProyectoService -> ProyectoRepository: next_version_number()
1.5 ProyectoService -> ProyectoRepository: add()
```

### Condiciones alternativas: Proyecto no encontrado / Snapshot invalido

Mensajes:
```text
2 [proyectoNoExiste] ProyectoService -> ProyectoRepository: get()
2.1 [proyectoNoExiste] ProyectoRepository -> ProyectoService: ProjectOrNull
2.2 [proyectoNoExiste] ProyectoService -> colaborativo: mostrarError()
3 [snapshotInvalido] colaborativo -> colaborativo: validarSnapshot()
3.1 [snapshotInvalido] colaborativo -> editor: mostrarError()
```




