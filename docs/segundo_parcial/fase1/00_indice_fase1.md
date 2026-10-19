# Fase 1 - Contratos, persistencia y migraciones

## Objetivo

Establecer la base versionada y persistente de la segunda parte de CASE Inteligente sin reemplazar los flujos del primer parcial. La fase incorpora contratos para especificaciones funcionales de metodos UML, asistente unico por proyecto, tema Flutter, snapshots V2, WebSocket V2 y lecturas moviles.

## Documentos

1. [Decisiones de modelado](01_decisiones_modelado.md)
2. [Contratos REST](02_contratos_rest.md)
3. [Contratos WebSocket](03_contratos_websocket.md)
4. [Modelo de persistencia](04_modelo_persistencia.md)
5. [Migraciones y compatibilidad](05_migraciones_compatibilidad.md)
6. [Pruebas de la fase](06_pruebas_fase1.md)
7. [Resumen y cierre](07_resumen_fase1.md)

## Entregables implementados

- Siete tablas nuevas mediante Alembic.
- Contratos Pydantic y TypeScript equivalentes.
- Servicios con autenticacion, membresia, roles, aislamiento e idempotencia.
- Endpoints REST reales de lectura y configuracion.
- Esquema WebSocket v2 compatible con clientes v1.
- Snapshot V2 con adaptador V1.
- Tema persistente conectado al generador Flutter.
- Especificacion de metodo integrada al modelo UML interno y restaurable.
- Proyecciones moviles de solo lectura.

