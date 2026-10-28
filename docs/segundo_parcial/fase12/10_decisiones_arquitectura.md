# Decisiones de arquitectura

## ADR-12-01: documento por version

Se eligio un documento independiente por snapshot. Evita arreglos BSON sin limite, permite indices por version y conserva inmutabilidad.

## ADR-12-02: registro SQL minimo

PostgreSQL conserva numero, autor, proyecto, revision, estado, hash e idempotencia. Esto mantiene permisos, listados y auditoria transaccional sin duplicar consultas administrativas en MongoDB.

## ADR-12-03: Outbox en vez de escritura dual directa

MongoDB no participa en la transaccion SQL. El Outbox evita estados confirmados a medias y admite reintentos con recibos idempotentes.

## ADR-12-04: normalizacion de legado al migrar

Los snapshots v1 se leen con el adaptador oficial y se almacenan como contenido efectivo v2. El JSONB original queda intacto para trazabilidad.

## ADR-12-05: retiro diferido

No se elimina `project_versions.snapshot` en Fase 12. Primero deben estabilizarse versiones y luego el documento UML editable en Fase 13.
