# Integracion Flutter

## Tema generado

`app_theme.dart` construye `ThemeData` claro y oscuro, `ColorScheme`, tipografia, AppBar, inputs, cards, botones, FAB, switches, dialogos, NavigationBar y Drawer. `main.dart` declara `theme`, `darkTheme` y `themeMode`.

Las pantallas CRUD consumen temas de componente. Los formularios respetan variante, radio y visibilidad de etiquetas; `PrimaryActionButton` respeta la variante. La densidad alimenta `VisualDensity` y la tipografia usa escala y peso discretos.

## Evidencia en artefacto

Cada proyecto contiene:

- `theme_manifest.json`: tema v2 efectivo.
- `ui_manifest.json`: estructura funcional visible.
- `generation-plan.json`: contrato coordinado, cuando corresponde.
- Manifiesto de generacion con `theme_contract_version` y SHA-256 estable.

El generador ejecuta `dart format` cuando Dart esta disponible antes de calcular checksums y crear el ZIP.
