# Decisiones de arquitectura

## ADR-13.1: agregado por diagrama

Se eligio un documento por diagrama porque proyecto y diagrama son uno a uno en el dominio actual. Permite leer el lienzo consistentemente y calcular un hash unico.

## ADR-13.2: registro SQL conservado

PostgreSQL conserva `uml_diagrams` para navegacion, permisos, auditoria y referencias de generaciones. Retirarlo en esta fase mezclaria migracion documental con rediseno administrativo.

## ADR-13.3: Outbox en lugar de transaccion distribuida

No se usa una transaccion 2PC entre PostgreSQL y MongoDB. Outbox entrega al menos una vez, con idempotencia, revision monotona y reconciliacion observable.

## ADR-13.4: Mongo-first con fallback reversible

La lectura principal cambia mediante bandera. Una revision Mongo menor que la revision SQL indica un evento pendiente y usa temporalmente SQL para ofrecer read-your-writes.

## ADR-13.5: cambios por ID

Las revisiones consecutivas actualizan elementos identificados mediante `arrayFilters`. Los cambios estructurales sustituyen el arreglo involucrado para preservar orden canonico y hash. El reemplazo completo queda para carga inicial, saltos de revision o importacion masiva.
