# Detalle procedimental para diagramas de clase dinamicos

Este documento sirve como guia textual para dibujar los DCD en Enterprise Architect. No usa PlantUML.

Formato de cada clase:

```text
NombrePaquete::NombreClase
--------------------------------
Atributos del dominio o BD
--------------------------------
Metodos del codigo
```

Criterio usado:

- Los atributos representan datos del dominio o BD.
- No se colocan controles visuales como `btn...` o `jTextField...`.
- No se colocan referencias internas como `negocio`, `modelo` o `conexion`.
- Los metodos se muestran con `+` porque fueron cambiados a `public` en el codigo.
- Las flechas siguen la arquitectura: `Presentacion -> Negocio -> Datos -> Base`.

## CU01. Gestionar docentes

### Marco del diagrama

`class DCD CU01 Gestionar docentes`

### Clase `Presentacion::PDocente`

Atributos:
```text
- idDocente : int
- idUsuario : int
- registro : String
- nombreCompleto : String
- nombreNormalizado : String
- correo : String
- password : String
```

Metodos:
```text
+ cargar() : void
+ seleccionado() : Docente
+ crearDocente(ActionEvent) : void
+ actualizarDocente(ActionEvent) : void
+ eliminarDocente(ActionEvent) : void
+ seleccionarDocente(MouseEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NDocente`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarDocentes() : List<Docente>
+ crearDocente(String, String, String, String) : void
+ actualizarDocente(Docente, String, String, String, String) : void
+ eliminarDocente(Docente) : void
```

### Clase `Negocio::UtilTexto`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ normalizarNombre(String) : String
```

### Clase `Datos::DUsuario`

Atributos:
```text
- idUsuario : int
- registro : String
- nombreCompleto : String
- nombreNormalizado : String
- correo : String
```

Metodos:
```text
+ crear(String, String, String, String) : int
+ actualizar(int, String, String, String, String) : void
+ eliminar(int) : void
```

### Clase `Datos::DDocente`

Atributos:
```text
- idDocente : int
- idUsuario : int
- password : String
```

Metodos:
```text
+ listar() : List<Docente>
+ obtenerPorId(int) : Docente
+ crear(int, String) : int
+ actualizar(int, String) : void
+ tieneCursos(int) : boolean
+ eliminar(int) : void
+ mapear(ResultSet) : Docente
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Relaciones

```text
Presentacion::PDocente -> Negocio::NDocente
Negocio::NDocente -> Datos::DUsuario
Negocio::NDocente -> Datos::DDocente
Negocio::NDocente -> Negocio::UtilTexto
Datos::DUsuario -> Base::Conexion
Datos::DDocente -> Base::Conexion
```

### Ubicacion sugerida

`PDocente` arriba, `NDocente` al centro, `UtilTexto` a un costado de negocio, `DUsuario` y `DDocente` abajo, `Conexion` abajo a la derecha.

## CU02. Gestionar estudiantes

### Marco del diagrama

`class DCD CU02 Gestionar estudiantes`

### Clase `Presentacion::PEstudiante`

Atributos:
```text
- idEstudiante : int
- idUsuario : int
- registro : String
- nombreCompleto : String
- nombreNormalizado : String
- correo : String
- telefono : String
- carrera : String
- plan : String
```

Metodos:
```text
+ cargar() : void
+ seleccionado() : Estudiante
+ limpiar() : void
+ crearEstudiante(ActionEvent) : void
+ actualizarEstudiante(ActionEvent) : void
+ eliminarEstudiante(ActionEvent) : void
+ importarCsv(ActionEvent) : void
+ seleccionarEstudiante(MouseEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NEstudiante`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarEstudiantes() : List<Estudiante>
+ obtenerPorRegistro(String) : Estudiante
+ crearEstudiante(String, String, String, String, String, String) : void
+ crearEstudianteYObtener(String, String, String, String, String, String) : Estudiante
+ actualizarEstudiante(Estudiante, String, String, String, String, String, String) : void
+ eliminarEstudiante(Estudiante) : void
+ importarCsv(File) : int
```

### Clase `Negocio::UtilTexto`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ normalizarNombre(String) : String
```

### Clase `Datos::DUsuario`

Atributos:
```text
- idUsuario : int
- registro : String
- nombreCompleto : String
- nombreNormalizado : String
- correo : String
```

Metodos:
```text
+ crear(String, String, String, String) : int
+ actualizar(int, String, String, String, String) : void
+ eliminar(int) : void
```

### Clase `Datos::DEstudiante`

Atributos:
```text
- idEstudiante : int
- idUsuario : int
- telefono : String
- carrera : String
- plan : String
```

Metodos:
```text
+ listar() : List<Estudiante>
+ obtenerPorId(int) : Estudiante
+ obtenerPorRegistro(String) : Estudiante
+ crear(int, String, String, String) : int
+ actualizar(int, String, String, String) : void
+ tieneDatosAsociados(int) : boolean
+ eliminar(int) : void
+ mapear(ResultSet) : Estudiante
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Relaciones

```text
Presentacion::PEstudiante -> Negocio::NEstudiante
Negocio::NEstudiante -> Datos::DUsuario
Negocio::NEstudiante -> Datos::DEstudiante
Negocio::NEstudiante -> Negocio::UtilTexto
Datos::DUsuario -> Base::Conexion
Datos::DEstudiante -> Base::Conexion
```

### Ubicacion sugerida

`PEstudiante` arriba, `NEstudiante` al centro, `DUsuario` y `DEstudiante` abajo, `UtilTexto` a un costado de negocio, `Conexion` abajo a la derecha.

## CU03. Gestionar materias

### Marco del diagrama

`class DCD CU03 Gestionar materias`

### Clase `Presentacion::PMateria`

Atributos:
```text
- idMateria : int
- sigla : String
- nombre : String
```

Metodos:
```text
+ cargar() : void
+ seleccionado() : Materia
+ limpiar() : void
+ crearMateria(ActionEvent) : void
+ actualizarMateria(ActionEvent) : void
+ eliminarMateria(ActionEvent) : void
+ seleccionarMateria(MouseEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NMateria`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarMaterias() : List<Materia>
+ crearMateria(String, String) : void
+ actualizarMateria(Materia, String, String) : void
+ eliminarMateria(Materia) : void
```

### Clase `Datos::DMateria`

Atributos:
```text
- idMateria : int
- sigla : String
- nombre : String
```

Metodos:
```text
+ listar() : List<Materia>
+ obtenerPorId(int) : Materia
+ crear(String, String) : int
+ actualizar(int, String, String) : void
+ tieneCursos(int) : boolean
+ eliminar(int) : void
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Relaciones

```text
Presentacion::PMateria -> Negocio::NMateria
Negocio::NMateria -> Datos::DMateria
Datos::DMateria -> Base::Conexion
```

### Ubicacion sugerida

`PMateria` arriba, `NMateria` al centro, `DMateria` abajo, `Conexion` abajo a la derecha.

## CU04. Gestionar cursos e inscripciones

### Marco del diagrama

`class DCD CU04 Gestionar cursos e inscripciones`

### Clase `Presentacion::PCurso`

Atributos:
```text
- idCurso : int
- idMateria : int
- idDocente : int
- idEstudiante : int
- materia : String
- docente : String
- registro : String
- estudiante : String
- grupo : String
- gestion : String
```

Metodos:
```text
+ cargarCombos() : void
+ cargarCursos() : void
+ cursoSeleccionado() : Curso
+ cargarInscritos() : void
+ limpiar() : void
+ crearCurso(ActionEvent) : void
+ eliminarCurso(ActionEvent) : void
+ inscribirEstudiante(ActionEvent) : void
+ importarCsvAlCurso(ActionEvent) : void
+ seleccionarCurso(MouseEvent) : void
+ seleccionarInscrito(MouseEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NCurso`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarCursos() : List<Curso>
+ crearCurso(Materia, Docente, String, String) : void
+ inscribirEstudiante(Curso, Estudiante) : void
+ importarCsvEnCurso(Curso, File) : ResultadoImportacion
+ listarEstudiantes(Curso) : List<Estudiante>
+ eliminarCurso(Curso) : void
```

### Clase `Negocio::NCurso.ResultadoImportacion`

Atributos:
```text
+ leidos : int
+ creados : int
+ inscritos : int
+ omitidos : int
+ invalidos : int
```

Metodos:
```text
+ resumen() : String
```

### Clase `Negocio::NMateria`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarMaterias() : List<Materia>
```

### Clase `Negocio::NDocente`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarDocentes() : List<Docente>
```

### Clase `Negocio::NEstudiante`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarEstudiantes() : List<Estudiante>
+ obtenerPorRegistro(String) : Estudiante
+ crearEstudianteYObtener(String, String, String, String, String, String) : Estudiante
```

### Clase `Datos::DCurso`

Atributos:
```text
- idCurso : int
- idMateria : int
- idDocente : int
- grupo : String
- gestion : String
```

Metodos:
```text
+ listar() : List<Curso>
+ obtenerPorId(int) : Curso
+ crear(int, int, String, String) : int
+ inscribirEstudiante(int, int) : void
+ estaInscrito(int, int) : boolean
+ listarEstudiantes(int) : List<Estudiante>
+ tieneDependencias(int) : boolean
+ eliminar(int) : void
+ mapear(ResultSet) : Curso
```

### Clase `Datos::DMateria`

Atributos:
```text
- idMateria : int
- sigla : String
- nombre : String
```

Metodos:
```text
+ listar() : List<Materia>
```

### Clase `Datos::DDocente`

Atributos:
```text
- idDocente : int
- idUsuario : int
- registro : String
- nombreCompleto : String
```

Metodos:
```text
+ listar() : List<Docente>
```

### Clase `Datos::DEstudiante`

Atributos:
```text
- idEstudiante : int
- idUsuario : int
- registro : String
- nombreCompleto : String
```

Metodos:
```text
+ listar() : List<Estudiante>
+ obtenerPorRegistro(String) : Estudiante
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Relaciones

```text
Presentacion::PCurso -> Negocio::NCurso
Presentacion::PCurso -> Negocio::NMateria
Presentacion::PCurso -> Negocio::NDocente
Presentacion::PCurso -> Negocio::NEstudiante
Negocio::NCurso -> Datos::DCurso
Negocio::NCurso -> Negocio::NEstudiante
Negocio::NCurso -> Negocio::NCurso.ResultadoImportacion
Negocio::NMateria -> Datos::DMateria
Negocio::NDocente -> Datos::DDocente
Negocio::NEstudiante -> Datos::DEstudiante
Datos::DCurso -> Base::Conexion
Datos::DMateria -> Base::Conexion
Datos::DDocente -> Base::Conexion
Datos::DEstudiante -> Base::Conexion
```

### Ubicacion sugerida

`PCurso` arriba. `NCurso` al centro como clase principal. `NMateria`, `NDocente` y `NEstudiante` a los costados. `DCurso`, `DMateria`, `DDocente` y `DEstudiante` abajo. `Conexion` abajo a la derecha.

## CU05. Gestionar examenes

### Marco del diagrama

`class DCD CU05 Gestionar examenes`

### Clase `Presentacion::PExamen`

Atributos:
```text
- idExamen : int
- idCurso : int
- curso : String
- tipo : String
- fecha : Date
- horaInicio : Time
- horaFin : Time
- estado : String
```

Metodos:
```text
+ cargarCursos() : void
+ cargarExamenes() : void
+ cursoSeleccionadoCombo() : Curso
+ examenSeleccionado() : Examen
+ limpiar() : void
+ crearExamen(ActionEvent) : void
+ eliminarExamen(ActionEvent) : void
+ abrirExamen(ActionEvent) : void
+ cerrarExamen(ActionEvent) : void
+ tomarAsistencia(ActionEvent) : void
+ seleccionarExamen(MouseEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NExamen`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarExamenes() : List<Examen>
+ crearExamen(Curso, String, Date, Time, Time) : void
+ abrirExamen(Examen) : void
+ cerrarExamen(Examen) : void
+ eliminarExamen(Examen) : void
```

### Clase `Negocio::NCurso`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarCursos() : List<Curso>
```

### Clase `Datos::DExamen`

Atributos:
```text
- idExamen : int
- idCurso : int
- tipo : String
- fecha : Date
- horaInicio : Time
- horaFin : Time
- estado : String
```

Metodos:
```text
+ listar() : List<Examen>
+ obtenerPorId(int) : Examen
+ crear(int, String, Date, Time, Time) : int
+ cambiarEstado(int, String) : void
+ tieneAsistencias(int) : boolean
+ eliminar(int) : void
+ mapear(ResultSet) : Examen
```

### Clase `Datos::DCurso`

Atributos:
```text
- idCurso : int
- idMateria : int
- idDocente : int
- grupo : String
- gestion : String
```

Metodos:
```text
+ listar() : List<Curso>
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Relaciones

```text
Presentacion::PExamen -> Negocio::NExamen
Presentacion::PExamen -> Negocio::NCurso
Presentacion::PExamen -> Presentacion::PAsistencia
Negocio::NExamen -> Datos::DExamen
Negocio::NCurso -> Datos::DCurso
Datos::DExamen -> Base::Conexion
Datos::DCurso -> Base::Conexion
```

### Ubicacion sugerida

`PExamen` arriba. `NExamen` debajo. `NCurso` a un lado. `DExamen` y `DCurso` abajo. `Conexion` abajo a la derecha.

## CU06. Generar QR de estudiante

### Marco del diagrama

`class DCD CU06 Generar QR de estudiante`

### Clase `Presentacion::PQR`

Atributos:
```text
- idEstudiante : int
- registro : String
- nombreCompleto : String
```

Metodos:
```text
+ cargar() : void
+ seleccionado() : Estudiante
+ descargarQr(ActionEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NQR`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ generarQrEstudiante(Estudiante, Path) : Path
```

### Clase `Negocio::NEstudiante`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarEstudiantes() : List<Estudiante>
```

### Clase `Datos::DEstudiante`

Atributos:
```text
- idEstudiante : int
- idUsuario : int
- registro : String
- nombreCompleto : String
- nombreNormalizado : String
- correo : String
- telefono : String
- carrera : String
- plan : String
```

Metodos:
```text
+ listar() : List<Estudiante>
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Clase externa opcional `QRCodeWriter`

Atributos:
```text
No registrar atributos.
```

Metodos:
```text
No registrar metodos; solo se dibuja como dependencia externa de `NQR`.
```

### Relaciones

```text
Presentacion::PQR -> Negocio::NEstudiante
Presentacion::PQR -> Negocio::NQR
Negocio::NEstudiante -> Datos::DEstudiante
Datos::DEstudiante -> Base::Conexion
Negocio::NQR -> QRCodeWriter
```

### Ubicacion sugerida

`PQR` arriba. `NEstudiante` y `NQR` al centro. `DEstudiante` abajo. `Conexion` abajo a la derecha. `QRCodeWriter` a la derecha como libreria externa.

## CU07. Registrar asistencia

### Marco del diagrama

`class DCD CU07 Registrar asistencia`

### Clase `Presentacion::PAsistencia`

Atributos:
```text
- idAsistencia : int
- idExamen : int
- idEstudiante : int
- registro : String
- estudiante : String
- fechaHora : Timestamp
- estado : String
- registroQr : String
- nombreQrNormalizado : String
```

Metodos:
```text
+ cargarTabla() : void
+ iniciarCamara() : void
+ detenerCamara() : void
+ procesarImagenCamara() : void
+ leerQr(BufferedImage) : String
+ justificar() : void
+ mostrarMensajeTemporal(String) : void
+ marcarAsistenciaManual(ActionEvent) : void
+ volver(ActionEvent) : void
```

### Clase `Negocio::NAsistencia`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ registrarPorQr(Examen, String) : void
+ registrarJustificado(Examen, Estudiante) : void
+ listarAsistencias(Examen) : List<Asistencia>
+ calcularEstado(Examen) : String
```

### Clase `Negocio::NCurso`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ listarEstudiantes(Curso) : List<Estudiante>
```

### Clase `Negocio::NEstudiante`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ obtenerPorRegistro(String) : Estudiante
```

### Clase `Negocio::UtilTexto`

Atributos:
```text
Sin atributos de dominio para dibujar.
```

Metodos:
```text
+ normalizarNombre(String) : String
```

### Clase `Datos::DAsistencia`

Atributos:
```text
- idAsistencia : int
- idExamen : int
- idEstudiante : int
- fechaHora : Timestamp
- estado : String
- registroQr : String
- nombreQrNormalizado : String
```

Metodos:
```text
+ crear(int, int, String, String, String) : void
+ existe(int, int) : boolean
+ listarPorExamen(int) : List<Asistencia>
```

### Clase `Datos::DEstudiante`

Atributos:
```text
- idEstudiante : int
- idUsuario : int
- registro : String
- nombreCompleto : String
```

Metodos:
```text
+ obtenerPorRegistro(String) : Estudiante
```

### Clase `Datos::DCurso`

Atributos:
```text
- idCurso : int
- idMateria : int
- idDocente : int
- grupo : String
- gestion : String
```

Metodos:
```text
+ estaInscrito(int, int) : boolean
+ listarEstudiantes(int) : List<Estudiante>
```

### Clase `Base::Conexion`

Atributos:
```text
- URL : String
- USUARIO : String
- PASSWORD : String
```

Metodos:
```text
+ getConexion() : Connection
```

### Clases externas opcionales `Webcam` y `MultiFormatReader`

Atributos:
```text
No registrar atributos.
```

Metodos:
```text
No registrar metodos; solo se dibujan como dependencias externas de `PAsistencia`.
```

### Relaciones

```text
Presentacion::PAsistencia -> Negocio::NAsistencia
Presentacion::PAsistencia -> Negocio::NCurso
Presentacion::PAsistencia -> Negocio::NEstudiante
Presentacion::PAsistencia -> Webcam
Presentacion::PAsistencia -> MultiFormatReader
Negocio::NAsistencia -> Datos::DAsistencia
Negocio::NAsistencia -> Datos::DEstudiante
Negocio::NAsistencia -> Datos::DCurso
Negocio::NAsistencia -> Negocio::UtilTexto
Negocio::NCurso -> Datos::DCurso
Negocio::NEstudiante -> Datos::DEstudiante
Datos::DAsistencia -> Base::Conexion
Datos::DEstudiante -> Base::Conexion
Datos::DCurso -> Base::Conexion
```

### Ubicacion sugerida

`PAsistencia` arriba. `NAsistencia` al centro como clase principal. `NCurso`, `NEstudiante` y `UtilTexto` a los costados. `DAsistencia`, `DEstudiante` y `DCurso` abajo. `Conexion` abajo a la derecha. `Webcam` y `MultiFormatReader` a la derecha como librerias externas.
