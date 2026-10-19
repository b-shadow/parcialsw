# Pruebas y fidelidad

## Capas

- Backend: adaptación, normalizacion, contraste, extras, manifiesto, salida Flutter y OpenAPI.
- React: recetas, contraste, adaptación v1, muestras por tipo y workspace con manifiesto real.
- Playwright: móvil, tablet y escritorio, modo oscuro, texto 160 %, labels largos y overflow.
- Flutter real: `pub get`, formato, `analyze`, widgets, golden de tokens semanticos y build web.
- Regresion: toda la suite backend/frontend y generacion coordinada Fase 5.

## Matriz

| Propiedad | Contrato | React | Flutter | Evidencia |
| --- | --- | --- | --- | --- |
| `light.primary` | tema v2 | paleta CSS | `ColorScheme.primary` | contraste + test de tema |
| `dark.primary` | tema v2 | modo oscuro | `darkTheme` | Playwright + Flutter |
| `button_style` | receta | boton preview | `PrimaryActionButton` | unitario + regresion |
| `navigation_style` | receta | barra/drawer | `NavigationBar`/`Drawer` | Playwright + Flutter |
| campo date | ui_manifest | muestra fecha | `showDatePicker` | manifest + generador |
| referencia | ui_manifest | selector | dropdown expandido | tests de asociacion |

## Comandos

```powershell
cd backend
$env:PYTHONPATH='../ai-engine'
uv run pytest -q

cd ../frontend
npm test -- --run
npm run lint
npm run build
npm run test:e2e
```

El proyecto generado incluye `test/goldens/theme_tokens.png`, construido deterministicamente desde los tokens efectivos claro, oscuro y error. Se verifica con `dart format --set-exit-if-changed lib test`, `flutter analyze`, `flutter test` y `flutter build web --release`.
