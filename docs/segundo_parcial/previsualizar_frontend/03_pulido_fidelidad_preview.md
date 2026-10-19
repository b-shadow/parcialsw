# Pulido de fidelidad del preview

## Ajuste realizado

La previsualizacion se ajusto para representar las mismas piezas que genera Flutter:

- `AppBar` con `primary_color`.
- Fondo de `Scaffold` con `background_color`.
- Cards/ListTile con `surface_color` y `border_radius`.
- Campos de formulario con borde y radio heredados de `InputDecorationTheme`.
- Dropdown de relacion.
- Switch con `button_color`.
- Boton principal con el mismo estilo que `PrimaryActionButton`.
- Boton flotante con `button_color`.

## Correccion importante

El formulario Flutter generado usaba `FilledButton` directamente. Eso hacia que el preview pudiera mostrar `outline` o `tonal`, pero el ZIP final no necesariamente lo replicara. Se corrigio el template para importar y usar:

```dart
PrimaryActionButton(
  onPressed: _save,
  label: 'Guardar',
)
```

Ahora el preview y el proyecto generado comparten la misma decision de estilo:

- `filled` -> `FilledButton`
- `outline` -> `OutlinedButton`
- `tonal` -> `FilledButton.tonal`

## Validaciones defensivas

El generador normaliza el tema antes de crear archivos:

- Colores invalidos vuelven al valor por defecto.
- `border_radius` se limita entre `0` y `32`.
- `button_style` solo acepta `filled`, `outline` o `tonal`.
- `density` solo acepta `compact`, `normal` o `comfortable`.

Esto evita que una configuracion incompleta o malformada rompa el ZIP Flutter.

## Verificacion esperada

Al generar Flutter con estilo personalizado, revisar:

- `lib/shared/themes/app_theme.dart`
- `lib/shared/widgets/primary_action_button.dart`
- `lib/modules/<modulo>/<modulo>_form_screen.dart`
- `README.md`
- `manifest.theme_config`

El boton del formulario debe usar `PrimaryActionButton` y el tema debe incluir `FloatingActionButtonThemeData`, `SwitchThemeData`, colores, fuente, radio y densidad.

