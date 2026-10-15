# Diseno de previsualizacion Flutter

## Objetivo

Permitir que el usuario configure el estilo visual del frontend Flutter antes de generar el ZIP. La previsualizacion debe ser inmediata dentro de CASE Inteligente y la configuracion seleccionada debe viajar al generador para crear codigo Flutter con el mismo tema.

## Alcance inicial

- Editar color primario.
- Editar color secundario.
- Editar color de fondo.
- Editar color de superficie.
- Editar color de botones.
- Seleccionar fuente.
- Seleccionar estilo de boton: solido, contorno o tonal.
- Ajustar radio de bordes.
- Ajustar densidad visual: compacta, normal o amplia.
- Ver una previsualizacion movil simple en la pantalla de generacion.

## Flujo

1. El usuario transforma un diagrama UML.
2. Genera el backend Spring Boot.
3. Ajusta el estilo Flutter en el panel de generacion.
4. Revisa la previsualizacion rapida.
5. Genera el frontend Flutter.
6. El backend recibe `theme_config` y lo aplica al proyecto generado.

## Datos enviados al backend

```json
{
  "theme_config": {
    "primary_color": "#0F766E",
    "secondary_color": "#14B8A6",
    "background_color": "#F8FAFC",
    "surface_color": "#FFFFFF",
    "button_color": "#0F766E",
    "font_family": "Roboto",
    "border_radius": 12,
    "button_style": "filled",
    "density": "normal"
  }
}
```

## Decision tecnica

La previsualizacion inicial es una maqueta web dentro de React. No compila Flutter en tiempo real porque eso seria mas lento y depende del SDK Flutter en la maquina. El ZIP generado si contiene el tema aplicado en `lib/shared/themes/app_theme.dart` y en el widget compartido `PrimaryActionButton`.

