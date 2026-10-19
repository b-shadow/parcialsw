# Fase 7 - Versionado, bitacora y notificaciones

## Objetivo cerrado

La fase integra tres historiales independientes: versiones manuales restaurables, actividad inmutable del proyecto y notificaciones dirigidas. La conversacion de IA conserva su propia secuencia y no retrocede durante una restauracion.

## Documentos

1. `01_arquitectura_versionado.md`: limites y componentes.
2. `02_snapshot_restauracion.md`: captura, hash, idempotencia y restauracion.
3. `03_bitacora_auditoria.md`: actividad de proyecto y auditoria.
4. `04_notificaciones_outbox_push.md`: bandeja, preferencias y entrega durable.
5. `05_api_websocket.md`: contratos HTTP y eventos en tiempo real.
6. `06_frontend_experiencia.md`: panel, dialogos y bandeja.
7. `07_seguridad_operacion.md`: permisos, secretos y operacion del outbox.
8. `08_pruebas_evidencia.md`: suites y resultados.
9. `09_resumen_fase7.md`: resultado arquitectonico.
10. `10_acta_cierre_fase7.md`: criterios de aceptacion.

## Implementacion principal

- `backend/migrations/versions/b8c2d3e4f5a6_phase7_versioning_notifications.py`
- `backend/app/modules/proyectos_colaboracion/services/project_service.py`
- `backend/app/modules/proyectos_colaboracion/services/project_mutation_guard.py`
- `backend/app/modules/notificaciones/services/notification_service.py`
- `backend/app/modules/notificaciones/services/outbox_dispatcher.py`
- `frontend/src/modules/gestion_proyectos_colaboracion/components/ProjectHistoryPanel.tsx`
- `frontend/src/shared/components/NotificationCenter.tsx`

