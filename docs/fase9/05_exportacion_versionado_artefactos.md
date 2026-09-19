# Exportacion y Versionado de Artefactos

## Salida en disco

Los proyectos Flutter generados se escriben en:

`storage/generated/flutter/{generation_id}/{package_name}`

Cada generacion usa el ID persistido de `GeneratedFrontend`, por lo que las salidas quedan aisladas por version.

## ZIP

El exportador crea:

`storage/generated/flutter/{generation_id}/{package_name}.zip`

El ZIP contiene la estructura completa del proyecto fuente Flutter generado.

## Manifiesto

El manifiesto persistido incluye:

- tecnologia: Flutter.
- lenguaje: Dart.
- nombre de proyecto.
- nombre de paquete.
- URL base de API.
- gestion de estado: Provider.
- capas generadas.
- cantidad de entidades.
- cantidad de archivos.
- ruta del ZIP.
- checksums SHA-256 por archivo fuente.
- origen de reglas de generacion.

## Persistencia

Cada archivo fuente se registra como `GeneratedArtifact` con tipo `flutter_source`.

El ZIP se registra como `GeneratedArtifact` con tipo `flutter_zip`.
