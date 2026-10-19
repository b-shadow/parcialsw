# Presets, fuentes y assets

## Presets

Los presets de sistema son inmutables: Profesional claro, Profesional oscuro y Academico. Los personalizados se almacenan en `flutter_theme_presets`, tienen nombre unico por proyecto sin distinguir mayusculas y un limite de 20.

Crear, modificar o eliminar exige rol Editor u Organizador. Todos los miembros pueden leer. Aplicar copia la configuracion al tema activo en una transaccion; eliminar un preset nunca elimina ni altera el tema activo.

## Fuentes

El catalogo v2 expone unicamente `system`. No se ofrecen fuentes remotas ni descarga en runtime, y tampoco se presupone que Roboto exista en todos los destinos. Una fuente adicional solo puede incorporarse junto con archivos, pesos, declaracion de `pubspec.yaml`, licencia y recurso equivalente para preview.

El editor anterior mostraba fuentes sin assets. Esa lista fue retirada para evitar una previsualizacion enganosa.
