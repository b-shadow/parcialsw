# Implementacion inicial

## Frontend CASE

Archivo principal:

- `frontend/src/modules/transformacion_generacion_software/pages/GenerationPage.tsx`

Se agrego un panel `Estilo Flutter` con:

- Presets: Profesional, Oscuro y Academico.
- Inputs de color para primario, secundario, fondo, superficie y botones.
- Selector de fuente.
- Selector de estilo de boton.
- Selector de densidad.
- Slider para radio de bordes.
- Preview movil inmediata.

El estado se guarda como `FlutterThemeConfig` y se envia al endpoint de generacion Flutter.

## Contrato TypeScript

Archivo:

- `frontend/src/modules/transformacion_generacion_software/types/generation.ts`

Se agrego el tipo:

```ts
export type FlutterThemeConfig = {
  primary_color: string;
  secondary_color: string;
  background_color: string;
  surface_color: string;
  button_color: string;
  font_family: string;
  border_radius: number;
  button_style: "filled" | "outline" | "tonal";
  density: "compact" | "normal" | "comfortable";
};
```

## Backend FastAPI

Archivo:

- `backend/app/modules/generacion_software/schemas/generation.py`

Se agrego `FlutterThemeConfig` como parte opcional de `FrontendGenerationRequest`. Los colores se validan como hexadecimal `#RRGGBB`, el radio se limita de `0` a `32`, y los estilos quedan restringidos a valores conocidos.

## Generador Flutter

Archivos:

- `backend/app/modules/generacion_software/flutter_generator/uml_analyzer/model_analyzer.py`
- `backend/app/modules/generacion_software/flutter_generator/services/flutter_generator_service.py`
- `backend/app/modules/generacion_software/flutter_generator/generator/project_writer.py`
- `backend/app/modules/generacion_software/flutter_generator/templates/flutter_templates.py`

El modelo interno `FlutterProject` ahora incluye `theme_config`. El generador escribe esos valores en:

- `lib/shared/themes/app_theme.dart`
- `lib/shared/widgets/primary_action_button.dart`
- `README.md`
- `manifest` de generacion

## Prueba agregada

Archivo:

- `backend/tests/test_phase9_flutter_generator.py`

La prueba `test_flutter_generator_applies_theme_config` valida que:

- El color primario aparece como `Color(0xFF...)`.
- El color de boton se renderiza.
- La fuente queda configurada.
- El radio de borde llega a `AppTheme`.
- La densidad visual llega a Flutter.
- El boton compartido cambia a `OutlinedButton` cuando el estilo es `outline`.
- El manifest conserva `theme_config`.

