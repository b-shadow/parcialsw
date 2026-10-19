# Pruebas de fase 5

## Casos especificos

`test_second_part_phase5_coordinated_generation.py` comprueba:

1. Plan determinista y contrato compartido.
2. Bloqueo de borradores antes de escribir.
3. Generacion de ambos proyectos y bundle atomico.
4. Deteccion de deriva de rutas.
5. Exposicion del ciclo coordinado en OpenAPI.

La prueba frontend verifica preflight, idempotencia, opciones de verificacion y descarga del bundle.

## Regresion ejecutada

| Componente | Resultado |
| --- | --- |
| Backend Ruff | aprobado |
| Backend Pytest | 69 passed |
| AI Engine Ruff | aprobado |
| AI Engine Pytest | 43 passed, 1 skipped por dependencia opcional |
| Frontend ESLint | aprobado |
| Frontend Vitest | 27 passed |
| Frontend TypeScript/Vite/PWA | build aprobado |

## Proyecto generado real

El fixture `Academico` incluye Estudiante, Curso, Inscripcion, asociacion muchos-a-muchos con clase de asociacion, UUID, LocalDate, Double, permisos, rango, requerido, unicidad, confirmacion y selectores.

| Comando | Resultado |
| --- | --- |
| `mvn test` | aprobado |
| `mvn package -DskipTests` | aprobado |
| `flutter analyze` | sin incidencias |
| `flutter test` | 2 passed |
| `flutter build web --release` | aprobado |
