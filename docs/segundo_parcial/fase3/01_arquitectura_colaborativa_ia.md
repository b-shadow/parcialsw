# Arquitectura colaborativa de IA

## Limites de responsabilidad

La capa REST crea y consulta estado durable. PostgreSQL conserva conversacion, mensajes, acciones, recomendaciones, resumen y eventos. WebSocket distribuye cambios ya confirmados y presencia efimera. El frontend combina una carga inicial REST con eventos incrementales.

```text
ProjectAiAssistant
  -> REST /projects/{id}/ai/*
  -> ProjectSocketClient /ws/projects/{id}
       -> ConnectionManager

ProjectAiApplicationService
  -> AssistantContractService / Repository
  -> UnifiedAiOrchestrator
  -> commit de mensajes, acciones y recomendaciones
  -> ProjectAiEventPublisher
       -> CollaborationEvent
       -> broadcast WebSocket
       -> push solo si es relevante
```

## Consistencia

1. La operacion de negocio valida membresia y permisos.
2. El estado se confirma en base de datos.
3. Se registra un `CollaborationEvent` con secuencia exclusiva del proyecto.
4. Se emite el sobre WebSocket v2.
5. Si el socket falla, la operacion durable permanece y el cliente la recupera por REST.

Nunca se publica como aplicado un cambio que no haya sido confirmado. Un fallo de push tampoco revierte ni hace fallar una accion ya persistida.

## Conversacion e identidad

`ai_conversations.project_id` es unico, por lo que un proyecto posee una sola conversacion activa compartida. Cada mensaje de usuario guarda `author_user_id`; la API agrega `author_display_name`. Los mensajes del motor se identifican como `Asistente CASE`.

## Concurrencia e idempotencia

- `client_message_id` evita repetir una consulta enviada por reintento.
- `idempotency_key` evita ejecutar dos veces una accion.
- El bloqueo de conversacion asigna secuencias sin colision.
- El bloqueo de accion serializa confirmaciones simultaneas.
- El store del frontend fusiona por ID y nunca retrocede cursores.
- Se limita por proyecto, por usuario y por cantidad global de inferencias.

## Seguridad

Toda ruta vuelve a verificar membresia. El WebSocket autentica mediante subprotocolo, valida origen y revalida usuario/membresia en cada heartbeat. El contexto solo incluye recursos del proyecto autorizado. Los roles de lectura no reciben acciones aplicables y los servicios de dominio vuelven a autorizar la ejecucion.
