# Contrato de tema v2

## Fuente de verdad

`FlutterThemeConfigV2` es estricto (`extra=forbid`) y se publica como JSON Schema. Contiene `schema_version`, `mode`, dos paletas completas, tipografia, radios y recetas de componentes. Los defaults versionados viven en `contracts/flutter_theme_defaults_v2.json` y su representacion ejecutable se valida al iniciar pruebas.

## Paletas

Cada modo declara `primary`, `secondary`, `background`, `surface`, `error`, `outline` y sus colores `on_*`. Los colores usan `#RRGGBB`, se serializan en mayusculas y no aceptan alfa. El servidor comprueba 4.5:1 en pares de texto y 3:1 para borde sobre superficie.

## Tipografia y forma

La unica fuente admitida inicialmente es `system`. De esta forma, web y Flutter usan una fuente presente en la plataforma, sin declarar archivos inexistentes ni depender de una CDN. La escala es discreta (`compact`, `normal`, `large`) y el peso base es `regular` o `medium`. Boton, campo, card y dialogo poseen radios independientes entre 0 y 24 px.

## Componentes

- Boton: `filled`, `outline`, `tonal`.
- Campo: `outline`, `filled`.
- Card: `flat`, `outlined`, `elevated`.
- Navegacion: `automatic`, `bottom_bar`, `navigation_drawer`.
- Densidad: `compact`, `normal`, `comfortable`.

Las recetas geometricas compartidas estan en `contracts/flutter_component_recipes_v1.json`. Ningun campo permite CSS, Dart o rutas arbitrarias.
