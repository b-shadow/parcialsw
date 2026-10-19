# Decisiones de modelado

## Una IA, varias intenciones

La solucion mantiene un solo asistente por proyecto. `AiMessage.detected_intents` admite varias intenciones para una solicitud compuesta, sin crear personalidades ni conversaciones separadas. La inferencia real queda para la Fase 2; esta fase no fabrica respuestas del modelo.

## Conversacion compartida

Existe una conversacion principal por proyecto. Se crea perezosamente con restriccion unica. La secuencia se asigna bloqueando la fila de conversacion y se vuelve a comprobar `client_message_id` despues del bloqueo para soportar reintentos concurrentes.

## Especificacion uno a uno

La firma UML continua en `uml_methods`. Su semantica vive en `uml_method_specifications`, con `method_id` unico y cascada. Esto permite que metodos antiguos sin especificacion sigan abriendo, validando y generando como antes.

La especificacion forma parte de `UmlMethodModel`; por ello se conserva al crear versiones, restaurar diagramas y transportar el modelo interno a generadores.

## JSONB tipado

Cada JSONB nuevo tiene esquema Pydantic asociado. Las reglas simples se normalizan a `{code, description, severity}`. Las configuraciones rechazan claves sensibles, y los contratos visibles validan ruta, verbo, controles y parametros UML.

## Tema Flutter

Se reutiliza `FlutterThemeConfig`, ya usado por el generador. Un proyecto anterior obtiene valores por defecto al primer acceso. Cuando una generacion no envia tema, `GenerationService` usa el tema persistente; una configuracion explicita sigue teniendo prioridad.

## Snapshot V2

El snapshot incluye proyecto, diagramas, tema, configuracion de generacion y configuracion no sensible de IA. Excluye mensajes, acciones, recomendaciones, suscripciones push, tokens y secretos. Los snapshots sin version se interpretan como V1 y se adaptan antes de restaurar.

## Movil como proyeccion

Las rutas `/mobile` son consultas compactas sobre proyectos y UML existentes. No duplican entidades y no exponen escrituras. `unread_notification_count` se mantiene en cero mientras no exista persistencia de bandeja de notificaciones; Web Push por si solo no permite calcular mensajes no leidos.

## Rol global y rol de proyecto

Cada usuario mantiene exactamente un rol global en `user_roles`: `ADMINISTRADOR` o `EDITOR`. La restriccion unica sobre `user_id` evita acumulaciones y la API administrativa no acepta `ORGANIZADOR` como rol global.

La autoridad colaborativa se modela por separado en `project_members.project_role`. Al crear un proyecto, el propietario recibe una unica membresia `ORGANIZADOR` para ese proyecto; esta asignacion no altera su rol global. En otros proyectos el mismo usuario puede ser `EDITOR` u `ORGANIZADOR` segun su membresia.

