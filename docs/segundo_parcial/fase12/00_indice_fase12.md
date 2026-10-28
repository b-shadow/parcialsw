# Fase 12 - Indice

## Objetivo

Migrar los snapshots inmutables de versiones UML a MongoDB, manteniendo PostgreSQL como registro relacional y rollback temporal.

## Documentos

1. `01_arquitectura_funcional.md`: limites y autoridad de datos.
2. `02_modelo_documental_versiones.md`: contrato BSON e indices.
3. `03_inmutabilidad_outbox.md`: escritura atomica e idempotencia.
4. `04_migracion_historica.md`: lotes, checkpoints y verificacion.
5. `05_lectura_comparada_rollback.md`: seleccion de fuente y banderas.
6. `06_restauracion_versiones.md`: vista previa, respaldo y restauracion.
7. `07_despliegue_operacion.md`: orden de arranque y comandos.
8. `08_retencion_respaldo.md`: conservacion y recuperacion.
9. `09_pruebas_trazabilidad.md`: evidencia por criterio.
10. `10_decisiones_arquitectura.md`: ADR resumido.
11. `11_resumen_fase12.md`: resultado implementado.
12. `12_acta_cierre_fase12.md`: condiciones de cierre.
