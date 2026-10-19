# Matriz de trazabilidad

| CU | Caso de uso | Riesgo principal | Evidencia automatizada | Resultado |
|---|---|---|---|---|
| CU-01 | Registrar cuenta | Duplicado o hash inseguro | `test_phase4_contracts.py` y pruebas de acceso | Aprobado |
| CU-02 | Autenticacion | Token invalido o acceso indebido | `test_phase4_contracts.py`, headers y rutas protegidas | Aprobado |
| CU-03 | Perfil propio | Modificar otro usuario | suite backend y Vitest de acceso | Aprobado |
| CU-04 | Usuarios y roles globales | Escalacion de privilegios | routers/servicios bajo Pytest y rutas admin | Aprobado |
| CU-05 | Reportes | Agregacion inconsistente | suite frontend y contratos API | Aprobado |
| CU-06 | Bitacora | Fuga entre proyectos | fases 3 y 7, actividad paginada | Aprobado |
| CU-07 | Manual/asistente | Respuesta fuera de contexto | AI fase 2 y store del asistente | Aprobado |
| CU-08 | Proyectos | Propietario o revision incorrecta | fases 1, 3, 7 y 8 | Aprobado |
| CU-09 | Integrantes y permisos | IDOR o rol incorrecto | colaboracion, snapshot y movil | Aprobado |
| CU-10 | Versiones y cambios | Restore destructivo | fase 7 y E2E `phase7-versioning.spec.ts` | Aprobado |
| CU-11 | Editor UML | Perdida o desorden colaborativo | motor UML, WebSocket y pruebas frontend | Aprobado |
| CU-12 | UML por imagen | Resultado precargado | `test_image_uml_detector.py` | Aprobado con corpus automatizado |
| CU-13 | Importar/exportar XMI | Perdida de multiplicidad | `test_phase6_uml_engine.py` | Aprobado |
| CU-14 | Validar UML | Aceptar modelo inconsistente | motor UML y contratos de metodos | Aprobado |
| CU-15 | Transformar UML | Deriva del modelo intermedio | fases 1, 4 y 5 | Aprobado |
| CU-16 | Generar Spring Boot | Proyecto no compilable | gate Maven real de fase 9 | Aprobado |
| CU-17 | Generar Flutter | Formularios/IDs no compilables | gate Flutter real y pruebas de multiplicidad | Aprobado |
| CU-18 | IA local offline | Dependencia cloud o accion extra | 43 pruebas AI, fallback y proveedor simulado | Aprobado; Ollama real es suite ambiental |

## Extensiones del segundo parcial

| Fase | Capacidad | Evidencia |
|---|---|---|
| 1 | Contratos y persistencia | `test_second_part_phase1_contracts.py`, Alembic real |
| 2 | IA unica Ollama/Qwen | `test_phase2_unified_ai.py`, `test_second_part_phase2_ai.py` |
| 3 | Memoria colaborativa | `test_second_part_phase3_collaboration.py` |
| 4 | Metodos funcionales | `test_second_part_phase4_method_specifications.py` |
| 5 | Generacion coordinada | `test_second_part_phase5_coordinated_generation.py` |
| 6 | Editor visual Flutter | backend, Vitest y Playwright responsive |
| 7 | Versiones/notificaciones | backend, frontend y E2E de restauracion |
| 8 | Cliente Flutter reducido | backend, 4 tests Flutter y APK debug |

