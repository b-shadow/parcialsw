# Verificacion y compilacion

## Estados

- `verified`: todas las herramientas ejecutadas terminaron con codigo 0.
- `generated_unverified`: falta una herramienta y el usuario activo `allow_unverified`.
- `failed`: una compilacion, prueba o validacion fallo.
- `not_run`: verificacion desactivada explicitamente.

No se etiqueta un artefacto como verificado por el solo hecho de escribir archivos.

## Spring Boot

El verificador busca `mvnw` y luego `mvn`. Ejecuta `mvn -q test`, que compila produccion y pruebas. Para la certificacion manual de esta fase tambien se ejecuto `mvn -q package -DskipTests` con Maven 3.9.9 y Java 17.

## Flutter

Se ejecutan, en orden y con tiempo limite:

```text
flutter pub get
flutter analyze
flutter test
flutter build web --release
```

## Aislamiento

Los comandos se ejecutan sin shell interpolado, con argumentos separados, tiempo limite y salida truncada en el manifiesto. Variables sensibles conocidas se eliminan del entorno hijo.

## Resultado real

- Maven test: aprobado.
- Maven package: aprobado.
- Flutter analyze: sin incidencias.
- Flutter test: 2 pruebas aprobadas.
- Flutter build web release: aprobado.
