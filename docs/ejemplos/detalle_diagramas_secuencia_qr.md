# Detalle simplificado para diagramas de secuencia

Este documento indica como dibujar los diagramas de secuencia del Sistema de Control de Asistencia por QR en Enterprise Architect.

El estilo sigue los ejemplos compartidos:

- Un actor a la izquierda.
- Lifelines por capa.
- Flujo inicial de carga.
- Fragmentos `alt` para cada accion principal.
- Mensajes resumidos, sin detallar todas las validaciones internas.
- Retornos punteados con tipos generales como `ArrayList`, `boolean`, `void`, `Connection`.

Convencion visual:

```text
Actor -> Presentacion -> Negocio -> Datos -> Base::Conexion
```

## CU01. Gestionar docentes

### Diagrama

`sd CU01 Gestionar docentes`

### Lifelines

```text
Administrador
Presentacion::PDocente
Negocio::NDocente
Negocio::UtilTexto
Datos::DDocente
Datos::DUsuario
Base::Conexion
```

### Flujo inicial

```text
PDocente -> PDocente: cargar()
PDocente -> NDocente: listarDocentes()
NDocente -> DDocente: listar()
DDocente -> Conexion: getConexion()
Conexion --> DDocente: Connection
DDocente --> NDocente: ArrayList
NDocente --> PDocente: ArrayList
```

### alt Crear

```text
Administrador -> PDocente: crearDocente()
PDocente -> NDocente: crearDocente(registro, nombre, correo, password)
NDocente -> UtilTexto: normalizarNombre(nombre)
UtilTexto --> NDocente: String
NDocente -> DUsuario: crear(registro, nombre, nombreNormalizado, correo)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NDocente: int
NDocente -> DDocente: crear(idUsuario, password)
DDocente -> Conexion: getConexion()
Conexion --> DDocente: Connection
DDocente --> NDocente: int
NDocente --> PDocente: void
PDocente -> PDocente: cargar()
```

### alt Modificar

```text
Administrador -> PDocente: actualizarDocente()
PDocente -> PDocente: seleccionado()
PDocente -> NDocente: actualizarDocente(docente, registro, nombre, correo, password)
NDocente -> UtilTexto: normalizarNombre(nombre)
UtilTexto --> NDocente: String
NDocente -> DUsuario: actualizar(idUsuario, registro, nombre, nombreNormalizado, correo)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NDocente: void
NDocente -> DDocente: actualizar(idDocente, password)
DDocente -> Conexion: getConexion()
Conexion --> DDocente: Connection
DDocente --> NDocente: void
NDocente --> PDocente: void
PDocente -> PDocente: cargar()
```

### alt Eliminar

```text
Administrador -> PDocente: eliminarDocente()
PDocente -> PDocente: seleccionado()
PDocente -> NDocente: eliminarDocente(docente)
NDocente -> DDocente: tieneCursos(idDocente)
DDocente -> Conexion: getConexion()
Conexion --> DDocente: Connection
DDocente --> NDocente: boolean
NDocente -> DDocente: eliminar(idDocente)
DDocente -> Conexion: getConexion()
Conexion --> DDocente: Connection
DDocente --> NDocente: void
NDocente -> DUsuario: eliminar(idUsuario)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NDocente: void
NDocente --> PDocente: void
PDocente -> PDocente: cargar()
```

## CU02. Gestionar estudiantes

### Diagrama

`sd CU02 Gestionar estudiantes`

### Lifelines

```text
Administrador
Presentacion::PEstudiante
Negocio::NEstudiante
Negocio::UtilTexto
Datos::DEstudiante
Datos::DUsuario
Base::Conexion
```

### Flujo inicial

```text
PEstudiante -> PEstudiante: cargar()
PEstudiante -> NEstudiante: listarEstudiantes()
NEstudiante -> DEstudiante: listar()
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: ArrayList
NEstudiante --> PEstudiante: ArrayList
```

### alt Crear

```text
Administrador -> PEstudiante: crearEstudiante()
PEstudiante -> NEstudiante: crearEstudiante(registro, nombre, correo, telefono, carrera, plan)
NEstudiante -> UtilTexto: normalizarNombre(nombre)
UtilTexto --> NEstudiante: String
NEstudiante -> DUsuario: crear(registro, nombre, nombreNormalizado, correo)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NEstudiante: int
NEstudiante -> DEstudiante: crear(idUsuario, telefono, carrera, plan)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: int
NEstudiante --> PEstudiante: void
PEstudiante -> PEstudiante: cargar()
PEstudiante -> PEstudiante: limpiar()
```

### alt Modificar

```text
Administrador -> PEstudiante: actualizarEstudiante()
PEstudiante -> PEstudiante: seleccionado()
PEstudiante -> NEstudiante: actualizarEstudiante(estudiante, registro, nombre, correo, telefono, carrera, plan)
NEstudiante -> UtilTexto: normalizarNombre(nombre)
UtilTexto --> NEstudiante: String
NEstudiante -> DUsuario: actualizar(idUsuario, registro, nombre, nombreNormalizado, correo)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NEstudiante: void
NEstudiante -> DEstudiante: actualizar(idEstudiante, telefono, carrera, plan)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: void
NEstudiante --> PEstudiante: void
PEstudiante -> PEstudiante: cargar()
PEstudiante -> PEstudiante: limpiar()
```

### alt Eliminar

```text
Administrador -> PEstudiante: eliminarEstudiante()
PEstudiante -> PEstudiante: seleccionado()
PEstudiante -> NEstudiante: eliminarEstudiante(estudiante)
NEstudiante -> DEstudiante: tieneDatosAsociados(idEstudiante)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: boolean
NEstudiante -> DEstudiante: eliminar(idEstudiante)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: void
NEstudiante -> DUsuario: eliminar(idUsuario)
DUsuario -> Conexion: getConexion()
Conexion --> DUsuario: Connection
DUsuario --> NEstudiante: void
NEstudiante --> PEstudiante: void
PEstudiante -> PEstudiante: cargar()
PEstudiante -> PEstudiante: limpiar()
```

### alt Importar CSV

```text
Administrador -> PEstudiante: importarCsv()
PEstudiante -> NEstudiante: importarCsv(archivo)
loop filas del CSV
NEstudiante -> DEstudiante: obtenerPorRegistro(registro)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: Estudiante/null
alt si no existe estudiante
NEstudiante -> NEstudiante: crearEstudiante(...)
NEstudiante --> PEstudiante: int
PEstudiante -> PEstudiante: cargar()
```

## CU03. Gestionar materias

### Diagrama

`sd CU03 Gestionar materias`

### Lifelines

```text
Administrador
Presentacion::PMateria
Negocio::NMateria
Datos::DMateria
Base::Conexion
```

### Flujo inicial

```text
PMateria -> PMateria: cargar()
PMateria -> NMateria: listarMaterias()
NMateria -> DMateria: listar()
DMateria -> Conexion: getConexion()
Conexion --> DMateria: Connection
DMateria --> NMateria: ArrayList
NMateria --> PMateria: ArrayList
```

### alt Crear

```text
Administrador -> PMateria: crearMateria()
PMateria -> NMateria: crearMateria(sigla, nombre)
NMateria -> DMateria: crear(sigla, nombre)
DMateria -> Conexion: getConexion()
Conexion --> DMateria: Connection
DMateria --> NMateria: int
NMateria --> PMateria: void
PMateria -> PMateria: cargar()
PMateria -> PMateria: limpiar()
```

### alt Modificar

```text
Administrador -> PMateria: actualizarMateria()
PMateria -> PMateria: seleccionado()
PMateria -> NMateria: actualizarMateria(materia, sigla, nombre)
NMateria -> DMateria: actualizar(idMateria, sigla, nombre)
DMateria -> Conexion: getConexion()
Conexion --> DMateria: Connection
DMateria --> NMateria: void
NMateria --> PMateria: void
PMateria -> PMateria: cargar()
PMateria -> PMateria: limpiar()
```

### alt Eliminar

```text
Administrador -> PMateria: eliminarMateria()
PMateria -> PMateria: seleccionado()
PMateria -> NMateria: eliminarMateria(materia)
NMateria -> DMateria: tieneCursos(idMateria)
DMateria -> Conexion: getConexion()
Conexion --> DMateria: Connection
DMateria --> NMateria: boolean
NMateria -> DMateria: eliminar(idMateria)
DMateria -> Conexion: getConexion()
Conexion --> DMateria: Connection
DMateria --> NMateria: void
NMateria --> PMateria: void
PMateria -> PMateria: cargar()
PMateria -> PMateria: limpiar()
```

## CU04. Gestionar cursos e inscripciones

### Diagrama

`sd CU04 Gestionar cursos e inscripciones`

### Lifelines

```text
Administrador
Presentacion::PCurso
Negocio::NCurso
Negocio::NMateria
Negocio::NDocente
Negocio::NEstudiante
Datos::DCurso
Base::Conexion
```

### Flujo inicial

```text
PCurso -> PCurso: cargarCombos()
PCurso -> NMateria: listarMaterias()
NMateria --> PCurso: ArrayList
PCurso -> NDocente: listarDocentes()
NDocente --> PCurso: ArrayList
PCurso -> NEstudiante: listarEstudiantes()
NEstudiante --> PCurso: ArrayList
PCurso -> PCurso: cargarCursos()
PCurso -> NCurso: listarCursos()
NCurso -> DCurso: listar()
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: ArrayList
NCurso --> PCurso: ArrayList
```

### alt Crear curso

```text
Administrador -> PCurso: crearCurso()
PCurso -> NCurso: crearCurso(materia, docente, grupo, gestion)
NCurso -> DCurso: crear(idMateria, idDocente, grupo, gestion)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: int
NCurso --> PCurso: void
PCurso -> PCurso: cargarCursos()
PCurso -> PCurso: limpiar()
```

### alt Eliminar curso

```text
Administrador -> PCurso: eliminarCurso()
PCurso -> PCurso: cursoSeleccionado()
PCurso -> NCurso: eliminarCurso(curso)
NCurso -> DCurso: tieneDependencias(idCurso)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: boolean
NCurso -> DCurso: eliminar(idCurso)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: void
NCurso --> PCurso: void
PCurso -> PCurso: cargarCursos()
```

### alt Seleccionar curso

```text
Administrador -> PCurso: seleccionarCurso()
PCurso -> PCurso: cargarInscritos()
PCurso -> NCurso: listarEstudiantes(curso)
NCurso -> DCurso: listarEstudiantes(idCurso)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: ArrayList
NCurso --> PCurso: ArrayList
```

### alt Inscribir estudiante

```text
Administrador -> PCurso: inscribirEstudiante()
PCurso -> NCurso: inscribirEstudiante(curso, estudiante)
NCurso -> DCurso: inscribirEstudiante(idCurso, idEstudiante)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: void
NCurso --> PCurso: void
PCurso -> PCurso: cargarInscritos()
```

### alt Importar CSV al curso

```text
Administrador -> PCurso: importarCsvAlCurso()
PCurso -> NCurso: importarCsvEnCurso(curso, archivo)
loop filas del CSV
NCurso -> NEstudiante: obtenerPorRegistro(registro)
NEstudiante --> NCurso: Estudiante/null
alt si no existe estudiante
NCurso -> NEstudiante: crearEstudianteYObtener(registro, nombre, correo, telefono, carrera, plan)
NEstudiante --> NCurso: Estudiante
NCurso -> DCurso: estaInscrito(idCurso, idEstudiante)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: boolean
alt si no esta inscrito
NCurso -> DCurso: inscribirEstudiante(idCurso, idEstudiante)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: void
NCurso --> PCurso: ResultadoImportacion
PCurso -> PCurso: cargarCombos()
PCurso -> PCurso: cargarInscritos()
```

## CU05. Gestionar examenes

### Diagrama

`sd CU05 Gestionar examenes`

### Lifelines

```text
Administrador
Presentacion::PExamen
Negocio::NExamen
Negocio::NCurso
Datos::DExamen
Base::Conexion
Presentacion::PAsistencia
```

### Flujo inicial

```text
PExamen -> PExamen: cargarCursos()
PExamen -> NCurso: listarCursos()
NCurso --> PExamen: ArrayList
PExamen -> PExamen: cargarExamenes()
PExamen -> NExamen: listarExamenes()
NExamen -> DExamen: listar()
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: ArrayList
NExamen --> PExamen: ArrayList
```

### alt Crear examen

```text
Administrador -> PExamen: crearExamen()
PExamen -> NExamen: crearExamen(curso, tipo, fecha, horaInicio, horaFin)
NExamen -> DExamen: crear(idCurso, tipo, fecha, horaInicio, horaFin)
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: int
NExamen --> PExamen: void
PExamen -> PExamen: cargarExamenes()
PExamen -> PExamen: limpiar()
```

### alt Abrir examen

```text
Administrador -> PExamen: abrirExamen()
PExamen -> NExamen: abrirExamen(examen)
NExamen -> DExamen: cambiarEstado(idExamen, "ABIERTO")
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: void
NExamen --> PExamen: void
PExamen -> PExamen: cargarExamenes()
```

### alt Cerrar examen

```text
Administrador -> PExamen: cerrarExamen()
PExamen -> NExamen: cerrarExamen(examen)
NExamen -> DExamen: cambiarEstado(idExamen, "CERRADO")
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: void
NExamen --> PExamen: void
PExamen -> PExamen: cargarExamenes()
```

### alt Eliminar examen

```text
Administrador -> PExamen: eliminarExamen()
PExamen -> NExamen: eliminarExamen(examen)
NExamen -> DExamen: tieneAsistencias(idExamen)
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: boolean
NExamen -> DExamen: eliminar(idExamen)
DExamen -> Conexion: getConexion()
Conexion --> DExamen: Connection
DExamen --> NExamen: void
NExamen --> PExamen: void
PExamen -> PExamen: cargarExamenes()
```

### alt Tomar asistencia

```text
Administrador -> PExamen: tomarAsistencia()
PExamen -> PExamen: examenSeleccionado()
PExamen -> PAsistencia: PAsistencia(examen)
PAsistencia --> PExamen: instancia
PExamen -> PAsistencia: setVisible(true)
```

## CU06. Generar QR de estudiante

### Diagrama

`sd CU06 Generar QR de estudiante`

### Lifelines

```text
Administrador
Presentacion::PQR
Negocio::NEstudiante
Negocio::NQR
Datos::DEstudiante
Base::Conexion
QRCodeWriter
```

### Flujo inicial

```text
PQR -> PQR: cargar()
PQR -> NEstudiante: listarEstudiantes()
NEstudiante -> DEstudiante: listar()
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: ArrayList
NEstudiante --> PQR: ArrayList
```

### alt Descargar QR

```text
Administrador -> PQR: descargarQr()
PQR -> PQR: seleccionado()
PQR -> NQR: generarQrEstudiante(estudiante, carpeta)
NQR -> QRCodeWriter: encode(...)
QRCodeWriter --> NQR: BitMatrix
NQR --> PQR: Path
PQR -> PQR: Mensajes.info()
```

## CU07. Registrar asistencia

### Diagrama

`sd CU07 Registrar asistencia`

### Lifelines

```text
Docente
Presentacion::PAsistencia
Negocio::NAsistencia
Negocio::NCurso
Negocio::NEstudiante
Negocio::UtilTexto
Datos::DAsistencia
Datos::DCurso
Datos::DEstudiante
Base::Conexion
Webcam
MultiFormatReader
```

### Flujo inicial

```text
PAsistencia -> PAsistencia: cargarTabla()
PAsistencia -> NAsistencia: listarAsistencias(examen)
NAsistencia -> DAsistencia: listarPorExamen(idExamen)
DAsistencia -> Conexion: getConexion()
Conexion --> DAsistencia: Connection
DAsistencia --> NAsistencia: ArrayList
NAsistencia --> PAsistencia: ArrayList
PAsistencia -> NCurso: listarEstudiantes(curso)
NCurso -> DCurso: listarEstudiantes(idCurso)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NCurso: ArrayList
NCurso --> PAsistencia: ArrayList
PAsistencia -> PAsistencia: iniciarCamara()
PAsistencia -> Webcam: open()
```

### loop Lectura QR

```text
PAsistencia -> Webcam: getImage()
Webcam --> PAsistencia: BufferedImage
PAsistencia -> MultiFormatReader: decode(bitmap)
MultiFormatReader --> PAsistencia: Result
PAsistencia -> NAsistencia: registrarPorQr(examen, lectura)
NAsistencia -> UtilTexto: normalizarNombre(nombreQr)
UtilTexto --> NAsistencia: String
NAsistencia -> DEstudiante: obtenerPorRegistro(registroQr)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NAsistencia: Estudiante
NAsistencia -> DCurso: estaInscrito(idCurso, idEstudiante)
DCurso -> Conexion: getConexion()
Conexion --> DCurso: Connection
DCurso --> NAsistencia: boolean
NAsistencia -> DAsistencia: existe(idExamen, idEstudiante)
DAsistencia -> Conexion: getConexion()
Conexion --> DAsistencia: Connection
DAsistencia --> NAsistencia: boolean
NAsistencia -> DAsistencia: crear(idExamen, idEstudiante, estado, registroQr, nombreQrNormalizado)
DAsistencia -> Conexion: getConexion()
Conexion --> DAsistencia: Connection
DAsistencia --> NAsistencia: void
NAsistencia --> PAsistencia: void
PAsistencia -> PAsistencia: cargarTabla()
```

### alt Marcar asistencia manual

```text
Docente -> PAsistencia: marcarAsistenciaManual()
PAsistencia -> NEstudiante: obtenerPorRegistro(registro)
NEstudiante -> DEstudiante: obtenerPorRegistro(registro)
DEstudiante -> Conexion: getConexion()
Conexion --> DEstudiante: Connection
DEstudiante --> NEstudiante: Estudiante
NEstudiante --> PAsistencia: Estudiante
PAsistencia -> NAsistencia: registrarJustificado(examen, estudiante)
NAsistencia -> DAsistencia: existe(idExamen, idEstudiante)
DAsistencia -> Conexion: getConexion()
Conexion --> DAsistencia: Connection
DAsistencia --> NAsistencia: boolean
NAsistencia -> DAsistencia: crear(idExamen, idEstudiante, "JUSTIFICADO", registro, nombreNormalizado)
DAsistencia -> Conexion: getConexion()
Conexion --> DAsistencia: Connection
DAsistencia --> NAsistencia: void
NAsistencia --> PAsistencia: void
PAsistencia -> PAsistencia: cargarTabla()
```

### alt Volver

```text
Docente -> PAsistencia: volver()
PAsistencia -> PAsistencia: detenerCamara()
PAsistencia -> Webcam: close()
Webcam --> PAsistencia: void
PAsistencia -> PAsistencia: dispose()
```

## Reglas para dibujarlo en Enterprise Architect

```text
1. Usar un marco por caso de uso: sd CUXX Nombre.
2. Dibujar lifelines en el orden indicado.
3. Usar flecha continua para llamadas.
4. Usar flecha punteada para retornos.
5. Encerrar cada accion en un fragmento alt.
6. Encerrar CSV y lectura de camara en loop.
7. No agregar validaciones internas si vuelven el diagrama demasiado cargado.
```
