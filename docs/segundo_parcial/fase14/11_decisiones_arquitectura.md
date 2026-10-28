# Decisiones de arquitectura

## ADR-14.1: retiro funcional antes del fisico

Se eliminaron primero las lecturas SQL de contenido. Tras aprobar el corte, `d2f6a7b8c9d0` ejecuta la purga fisica irreversible; el rollback consiste en restaurar el backup coordinado previo.

## ADR-14.2: gate basado en evidencia

Una bandera no prueba consistencia. El cambio exige migraciones, auditorias saludables y Outbox drenado, registrados en un checkpoint verificable.

## ADR-14.3: backup logico portable

Se usa un formato versionado independiente de binarios `pg_dump`/`mongodump`, disponible dentro de la imagen actual y comprobable por SHA-256. El destino normal debe estar vacio.

## ADR-14.4: reconciliacion no destructiva

El reconciliador detecta y alerta; no elimina huerfanos ni reescribe hashes. La reparacion automatica podria destruir la copia correcta durante una particion o carrera.

## ADR-14.5: PostgreSQL conserva registros

Los UUID de diagrama, version y conversacion siguen en SQL porque participan en permisos, navegacion, revision, auditoria y relaciones administrativas. El contenido variable permanece en MongoDB.
