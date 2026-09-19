# Pruebas del Generador Flutter

## Pruebas automatizadas backend

Se agrego `backend/tests/test_phase9_flutter_generator.py`.

La prueba valida:

- creacion de `pubspec.yaml`.
- creacion de `analysis_options.yaml`.
- creacion de `web/index.html` y `web/manifest.json`.
- creacion de `lib/main.dart`.
- generacion de ZIP.
- manifiesto Flutter/Dart.
- modelos con `fromJson` y `toJson`.
- servicios CRUD.
- providers con `ChangeNotifier`.
- formularios con `TextFormField` y `SwitchListTile`.
- rutas por modulo.
- registro OpenAPI del endpoint Flutter y descarga.

## Validaciones ejecutadas

- `backend/.venv/Scripts/python.exe -m ruff check app tests`
- `backend/.venv/Scripts/python.exe -m pytest`
- `frontend npm run lint`
- `frontend npm test -- --run`
- `frontend npm run build`
- `flutter pub get --offline`
- `flutter analyze`
- `flutter build web`

## Resultado

Todas las validaciones finalizaron correctamente. `flutter analyze` reporto cero issues y `flutter build web` construyo `build/web` en el proyecto de muestra.
