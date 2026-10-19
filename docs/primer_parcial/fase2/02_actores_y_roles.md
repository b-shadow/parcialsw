# Fase 2 - Actores y roles

## AC-01 Administrador

Actor humano con responsabilidad global sobre la plataforma.

Responsabilidades:

- Gestionar usuarios.
- Gestionar roles globales.
- Supervisar funcionamiento general.
- Consultar reportes globales.
- Consultar bitacoras administrativas.
- Mantener configuraciones generales.

Permisos globales:

- Administrar cuentas.
- Activar o desactivar usuarios.
- Asignar roles globales.
- Acceder a reportes administrativos.

Restricciones:

- No reemplaza automaticamente al Organizador de un proyecto salvo por funciones administrativas definidas.
- Sus acciones deben quedar auditadas.

## AC-02 Editor

Usuario que participa en proyectos colaborativos.

Responsabilidades:

- Crear proyectos.
- Editar diagramas UML segun permisos internos.
- Participar en sesiones colaborativas.
- Solicitar validaciones IA.
- Ejecutar generaciones si tiene permiso.
- Consultar informacion de proyectos donde participa.

Regla:

- Cuando un Editor crea un proyecto, se convierte automaticamente en Organizador de ese proyecto.

## AC-03 Organizador

Rol interno dentro de un proyecto. Un usuario puede ser Organizador en un proyecto y Editor en otro.

Responsabilidades:

- Administrar integrantes del proyecto.
- Gestionar permisos internos.
- Controlar versiones.
- Supervisar cambios.
- Autorizar acciones de generacion o exportacion si aplica.

Permisos internos:

- Gestionar integrantes.
- Editar configuracion del proyecto.
- Crear/restaurar versiones.
- Ver bitacora del proyecto.

## AS-01 Inteligencia Artificial Local

Actor secundario del sistema.

Responsabilidades:

- Interpretar instrucciones en lenguaje natural.
- Procesar texto proveniente de voz.
- Analizar imagenes de diagramas.
- Generar modelos UML estructurados.
- Validar diagramas.
- Apoyar transformacion y generacion de codigo.

Restriccion:

- Debe ejecutarse offline en el producto final.

## AS-02 Enterprise Architect

Sistema externo relacionado con intercambio de modelos UML mediante XMI.

Responsabilidades:

- Proveer modelos XMI importables.
- Recibir modelos XMI exportados.

Restriccion:

- Es integracion por archivo/formato, no dependencia central del funcionamiento de la plataforma.

