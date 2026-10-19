# Pruebas y evidencia

## Automatizadas

Ejecutadas el 17 de octubre de 2026:

```powershell
cd mobile
flutter analyze
flutter test
```

Resultado: analisis sin observaciones y 4 pruebas Flutter aprobadas.

```powershell
cd backend
$env:PYTHONPATH = '..\ai-engine'
uv run pytest tests/test_second_part_phase8_mobile.py tests/test_second_part_phase7_versioning_notifications.py -q
```

Resultado focalizado: 12 pruebas aprobadas. Regresion backend completa: 89 pruebas aprobadas. Se validan rutas, ausencia de mutaciones moviles, contrato de solo lectura y regresion de versiones/notificaciones.

## Compilacion

`flutter build apk --debug` finalizo correctamente. Artefacto: `mobile/build/app/outputs/flutter-apk/app-debug.apk`.

El motor de IA aprobo 43 pruebas y mantuvo 1 prueba omitida por condicion explicita.

## Cobertura funcional

| Area | Evidencia |
|---|---|
| Contratos | OpenAPI y modelos Dart |
| Solo lectura | Backend, rechazo en UI y test de widget |
| Componentes | Test `EmptyState` y analisis estatico |
| Cache | Serializacion reversible de proyecto/diagrama |
| Tiempo real | Estado, backoff, heartbeat y deduplicacion implementados |
| Seguridad | Token seguro y purga de cache al salir |

## Limitaciones del entorno

No habia Android/iPhone conectado durante el cierre. `flutter devices` detecto Windows, Chrome y Edge. La prueba tactil final en hardware queda como verificacion de aceptacion, no como implementacion pendiente.
