# Fase 5 - Generacion coordinada Spring Boot y Flutter

## Objetivo cerrado

La fase transforma el modelo intermedio v2 en dos proyectos coherentes usando un unico `GenerationPlan` inmutable. La generacion deja de interpretar metodos dos veces: Java y Dart consumen rutas, tipos, DTO, reglas, permisos y controles ya normalizados.

## Documentos

1. `01_generation_plan_compartido.md`: contrato canonico.
2. `02_preflight_y_diagnosticos.md`: bloqueo antes de escribir.
3. `03_generacion_spring_boot_funcional.md`: emision Java.
4. `04_generacion_flutter_funcional.md`: emision Dart.
5. `05_validacion_cruzada.md`: invariantes full stack.
6. `06_verificacion_compilacion.md`: herramientas y estados honestos.
7. `07_seguridad_artefactos.md`: publicacion, secretos y permisos.
8. `08_pruebas_fase5.md`: evidencias automatizadas y reales.
9. `09_guia_proyectos_generados.md`: uso del bundle.
10. `10_resumen_fase5.md`: resultado arquitectonico.
11. `11_acta_cierre_fase5.md`: criterios de cierre.

## Implementacion principal

- `backend/app/modules/generacion_software/coordinated_generator/`
- `backend/app/modules/generacion_software/models/coordinated_generation.py`
- `backend/migrations/versions/f6a0b3c4d5e6_phase5_coordinated_generation.py`
- `frontend/src/modules/transformacion_generacion_software/pages/GenerationPage.tsx`
- `backend/tests/test_second_part_phase5_coordinated_generation.py`
