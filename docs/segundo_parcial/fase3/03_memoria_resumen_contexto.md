# Memoria, resumen y contexto

## Memoria corta

`ProjectContextBuilder` toma hasta `max_context_messages` mensajes recientes en orden de conversacion. Incluye proyecto, actor, permisos, diagrama solicitado, versiones opcionales y acciones pendientes. El presupuesto de contexto y la sanitizacion de fase 2 siguen siendo obligatorios.

## Memoria larga

Al completar una interaccion se programa `summarize_project_conversation`. Cuando los mensajes no resumidos alcanzan `summary_trigger_messages`, se produce una estructura validada:

```text
project_goal
decisions
open_questions
recent_changes
important_entities
pending_actions
member_preferences_relevant_to_work
summary_until_sequence
```

El resumen se almacena como JSON en `ai_conversations.summary`. Los mensajes originales no se eliminan. La escritura usa bloqueo y compara el limite inicial, evitando que dos tareas sobrescriban resumenes concurrentes.

## Criterios de extraccion

La implementacion base es determinista y offline: conserva el objetivo, detecta expresiones de decision, preguntas abiertas, intenciones de modificacion, referencias y acciones propuestas. Deduplica sin distinguir mayusculas y aplica limites de longitud/cantidad antes de persistir.

## Integracion al contexto

En la siguiente consulta, el resumen se entrega como `conversation_summary`; los mensajes recientes cubren el tramo posterior y `generation_state.pending_actions` evita proponer como inexistente una operacion aun pendiente de confirmacion.

## Fallos

Un resumen invalido se ignora y se reconstruye. Si la frontera cambia durante el proceso, la tarea abandona sin escribir. Si el trabajo en segundo plano falla, la interaccion ya completada no se revierte y queda registrada para el siguiente intento.
