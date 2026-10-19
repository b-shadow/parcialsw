# Estructura Flutter Generada

## Archivos base

El generador produce un proyecto Flutter con:

- `pubspec.yaml`
- `analysis_options.yaml`
- `README.md`
- `web/index.html`
- `web/manifest.json`
- `lib/main.dart`
- `lib/core/network/api_client.dart`
- `lib/core/routes/app_router.dart`
- `lib/shared/themes/app_theme.dart`
- `lib/shared/widgets/primary_action_button.dart`

## Modulos por entidad

Por cada entidad UML se crean cinco archivos:

- modelo Dart.
- servicio HTTP CRUD.
- provider de estado.
- pantalla de listado.
- pantalla de formulario.

Ejemplo para `Cliente`:

- `lib/modules/cliente/cliente_model.dart`
- `lib/modules/cliente/cliente_service.dart`
- `lib/modules/cliente/cliente_provider.dart`
- `lib/modules/cliente/cliente_list_screen.dart`
- `lib/modules/cliente/cliente_form_screen.dart`

## Proyecto de muestra

Se genero una muestra validada en:

`storage/generated/flutter/phase9-sample/sistema_ventas_mobile`

El ZIP exportado quedo en:

`storage/generated/flutter/phase9-sample/sistema_ventas_mobile.zip`
