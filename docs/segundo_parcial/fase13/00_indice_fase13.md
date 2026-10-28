# Fase 13 - Indice

## Objetivo

Convertir MongoDB en la fuente principal de lectura del contenido UML activo, manteniendo PostgreSQL como registro, autoridad de permisos y proyeccion transaccional reversible durante la migracion.

## Documentos

1. `01_arquitectura_funcional.md`: limites y flujo entre almacenes.
2. `02_modelo_documental_activo.md`: agregado UML, identidad e indices.
3. `03_concurrencia_actualizaciones.md`: revisiones, cambios parciales e idempotencia.
4. `04_outbox_escritura_dual.md`: consistencia eventual y orden de eventos.
5. `05_migracion_reconciliacion.md`: lotes, checkpoint y hashes.
6. `06_integracion_funcional.md`: editor, XMI, IA, asistente y generadores.
7. `07_despliegue_operacion.md`: configuracion, arranque y observabilidad.
8. `08_rollback_recuperacion.md`: retorno controlado a SQL.
9. `09_pruebas_trazabilidad.md`: evidencia por criterio de cierre.
10. `10_decisiones_arquitectura.md`: decisiones y alternativas.
11. `11_resumen_fase13.md`: resultado implementado.
12. `12_acta_cierre_fase13.md`: aceptacion y alcance pendiente.
