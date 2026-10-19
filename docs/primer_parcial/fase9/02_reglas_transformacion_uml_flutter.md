# Reglas de Transformacion UML a Flutter

## Entidades

Cada clase UML del modelo intermedio se transforma en una entidad Dart:

- Clase `Cliente` -> modulo `lib/modules/cliente`.
- Modelo `Cliente` -> `cliente_model.dart`.
- Servicio REST -> `cliente_service.dart`.
- Provider -> `cliente_provider.dart`.
- Pantallas -> `cliente_list_screen.dart` y `cliente_form_screen.dart`.

## Campos

Los atributos UML se transforman a tipos Dart:

- `String`, `str`, `uuid` -> `String`.
- `Integer`, `int`, `long` -> `int`.
- `Double`, `float` -> `double`.
- `Boolean`, `bool` -> `bool`.
- `Date`, `DateTime` -> `DateTime`.

El campo `id` se trata como identificador comun y se genera como `String? id`.

## Formularios

La seleccion de controles se deriva del tipo:

- `bool` -> `SwitchListTile`.
- `int` y `double` -> `TextFormField` numerico.
- nombres con `correo` o `email` -> teclado email.
- `DateTime` -> entrada de texto parseable a fecha.
- otros campos -> entrada de texto.

## Serializacion

Cada modelo generado contiene:

- constructor inmutable.
- `fromJson(Map<String, dynamic>)`.
- `toJson()`.
- `copyWith`.

Las fechas se serializan con `toIso8601String()` y se parsean con `DateTime.tryParse`.

## Endpoints

Los servicios usan convencion REST compatible con fase 8:

- `GET /api/clientes`
- `GET /api/clientes/{id}`
- `POST /api/clientes`
- `PUT /api/clientes/{id}`
- `DELETE /api/clientes/{id}`
