# Prompt para generar diagrama UML de inscripcion

Crea un diagrama UML de clases para un sistema academico de inscripciones.

Debe tener exactamente estas clases:

Clase Estudiante:
- id: UUID
- nombre: String
- correo: String
- fechaRegistro: Date
- inscribirse(): void
- actualizarPerfil(): void

Clase Curso:
- id: UUID
- nombre: String
- descripcion: String
- duracionHoras: Integer
- agregarTema(): void
- obtenerDetalle(): void

Clase Inscripcion:
- id: UUID
- fecha: Date
- estado: String
- notaFinal: Double
- obtenerDetalle(): void

Relaciones:
- Estudiante y Curso tienen una relacion muchos a muchos.
- Usa Inscripcion como clase asociativa de la relacion entre Estudiante y Curso.
- La multiplicidad en ambos extremos debe ser *.
- La etiqueta de la relacion debe ser inscripcion.

Distribucion esperada:
- Estudiante a la izquierda.
- Curso a la derecha.
- Inscripcion abajo al centro, unida con linea discontinua a la relacion principal.
