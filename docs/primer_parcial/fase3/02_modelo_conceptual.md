# Fase 3 - Modelo conceptual

## Entidades principales

### Usuario

Representa una persona que accede a la plataforma.

Relaciones:

- Usuario tiene roles globales.
- Usuario crea proyectos.
- Usuario integra proyectos.
- Usuario genera versiones, eventos, procesos IA y artefactos.

### Rol

Representa permisos globales de plataforma.

Roles iniciales:

- `ADMINISTRADOR`
- `EDITOR`
- `ORGANIZADOR`

### Proyecto

Espacio colaborativo de trabajo.

Relaciones:

- Proyecto pertenece a un usuario propietario.
- Proyecto tiene integrantes.
- Proyecto tiene permisos internos.
- Proyecto tiene versiones.
- Proyecto tiene diagramas UML.
- Proyecto tiene eventos y generaciones.

### Integrante de proyecto

Relaciona usuario y proyecto.

Relaciones:

- Integrante pertenece a un proyecto.
- Integrante referencia un usuario.
- Integrante tiene permisos internos.

### Diagrama UML

Modelo UML persistido del proyecto.

Relaciones:

- Diagrama pertenece a proyecto.
- Diagrama tiene clases.
- Diagrama tiene relaciones.
- Diagrama tiene elementos visuales.
- Diagrama puede importarse/exportarse como XMI.

### Clase UML

Elemento principal de un diagrama de clases.

Relaciones:

- Clase pertenece a diagrama.
- Clase tiene atributos.
- Clase tiene metodos.
- Clase participa en relaciones.

### Relacion UML

Representa asociacion, herencia, implementacion, dependencia, agregacion o composicion entre clases.

### Version de proyecto

Snapshot versionado del estado del proyecto/modelo.

### Evento colaborativo

Registro ordenable de cambios emitidos durante sesiones colaborativas.

### Proceso IA

Registro de ejecucion de IA local: texto, voz, imagen, validacion o generacion.

### Transformacion UML

Resultado intermedio entre modelo UML y generadores.

### Backend generado

Registro de proyecto Spring Boot generado.

### Frontend generado

Registro de proyecto Flutter generado.

### Artefacto generado

Archivo exportable o paquete derivado de una generacion.

