# Pruebas y evidencia

## Cobertura agregada

- Hash determinista sin fecha de captura ni revision operativa.
- Contrato estricto contra campos desconocidos.
- Saneamiento profundo de auditoria.
- Deep links internos cerrados.
- Creacion atomica de bandeja y outbox con exclusion del actor.
- Unicidad de preferencias globales aun cuando `project_id` es nulo.
- Conteos de contenido UML para vista previa.
- Taxonomia canonica de eventos.
- Exposicion OpenAPI de versiones, actividad y bandeja.
- Resolucion frontend de destinos seguros.
- Compilacion TypeScript, PWA y service worker.
- Recorrido E2E de actividad, version manual y vista previa de restauracion.
- Contencion defensiva de colecciones IA malformadas para no desmontar la interfaz.

## Resultados ejecutados

| Suite | Resultado |
| --- | --- |
| Backend Pytest | 85 passed |
| Backend Ruff | sin hallazgos |
| Frontend Vitest | 36 passed |
| Frontend ESLint | sin hallazgos |
| Frontend build | correcto, PWA generada |
| Frontend Playwright E2E | 4 passed: fase 7 y editor visual en mobile, tablet y desktop |
| AI engine Pytest | 43 passed, 1 skipped por dependencia opcional |
| Alembic SQL | cadena completa y cabeza unica `b8c2d3e4f5a6` |

La migracion fue validada como SQL transaccional desde la revision inicial hasta la cabeza. El intento de aplicarla a PostgreSQL local no obtuvo respuesta; la base debe estar activa antes de ejecutar `alembic upgrade head`. Esto no se contabiliza como una migracion aplicada.

