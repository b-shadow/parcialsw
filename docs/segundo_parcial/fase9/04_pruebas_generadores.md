# Pruebas de generadores

## Fixture canonico

El gate genera `Estudiante`, `Curso` e `Inscripcion`. La relacion muchos a muchos usa `Inscripcion` como association class e incluye fecha, decimal y claves foraneas. El fixture obliga a ejercitar selectores, tipos de fecha, multiplicidades y DTO relacionados.

## Spring Boot

Comando ejecutado indirectamente por Pytest:

```powershell
mvn --batch-mode --no-transfer-progress test
```

Entorno: Maven 3.9.11 y OpenJDK 17.0.19. Resultado: proyecto generado y compilado sin cambios manuales, `1 passed` en 8.32 s.

## Flutter generado

Comandos ejecutados sobre una generacion nueva:

```powershell
flutter pub get
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build web
```

Resultado: todos los pasos aprobaron sin editar la salida, `1 passed` en 84.97 s. Se uso Flutter 3.44.1 y Dart 3.12.1.

## Contrato cruzado

Las pruebas de fases 5 y 6 comprobaron el mismo `canonical_hash`, rutas funcionales y DTO en Spring y Flutter. Las pruebas historicas verifican IDs por multiplicidad, selector de entidades, fechas y association classes. Los gates nuevos prueban ademas que las salidas son aceptadas por sus compiladores reales.

