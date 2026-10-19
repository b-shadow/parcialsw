# Arquitectura del Generador Flutter

## Alcance

La fase 9 implementa el generador de frontend Flutter dentro del modulo `generacion_software`, manteniendo la separacion definida en fases anteriores: FastAPI sigue siendo backend de la plataforma CASE y Flutter es un artefacto generado a partir del modelo UML transformado.

## Componentes implementados

- `uml_analyzer`: interpreta el modelo intermedio y construye entidades Dart.
- `api_analyzer`: deriva endpoints REST compatibles con el backend Spring Boot generado.
- `templates`: produce archivos Dart, YAML y web con contenido deterministicamente generado.
- `generator`: arma el conjunto de archivos y lo escribe en disco.
- `validators`: valida que el proyecto tenga paquete, entidades y campos consistentes.
- `exporter`: genera ZIP y checksums SHA-256.
- `services`: orquesta analisis, validacion, escritura, empaquetado y manifiesto.

## Flujo principal

1. `GenerationService.generate_frontend` recibe una transformacion existente.
2. Se valida membresia del usuario en el proyecto.
3. `FlutterGeneratorService` analiza el modelo intermedio.
4. Se generan archivos Flutter bajo `storage/generated/flutter/{generation_id}/{package_name}`.
5. Se crea un ZIP versionado junto al directorio del proyecto.
6. Se persiste `GeneratedFrontend` y se registran `GeneratedArtifact`.
7. La API expone descarga por `/generation/flutter/{frontend_id}/download`.

## Decisiones tecnicas

- Se usa Provider como gestion de estado por ser liviano, estable y suficiente para CRUD generado.
- La salida incluye configuracion `web/` para que el proyecto compile con `flutter build web`.
- El cliente HTTP generado usa `package:http` y mantiene soporte para token Bearer.
- El generador no modifica la arquitectura de base de datos existente; reutiliza `generated_frontends` y `generated_artifacts`.
