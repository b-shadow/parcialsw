# Memoria y contexto

## Documento `ai_context_snapshots`

Cada resumen contiene proyecto, conversación, límite de secuencia, resumen serializado, contexto estructurado, hash, versión y fechas UTC. El id se deriva de conversación y secuencia mediante UUID5, por lo que repetir el resumen produce el mismo documento.

## Generación

El servicio de memoria:

1. calcula mensajes no resumidos desde el contador SQL;
2. obtiene el historial acotado desde Mongo con superposición SQL;
3. conserva decisiones, preguntas, cambios, entidades y acciones pendientes;
4. sanea texto no confiable;
5. bloquea la conversación y comprueba que el límite inicial no cambió;
6. actualiza el fallback SQL y encola el snapshot Mongo en la misma transacción.

## Construcción de contexto

El asistente utiliza:

- últimos mensajes acotados por `max_context_messages`;
- snapshot Mongo más reciente de cada chat;
- fallback SQL si el snapshot todavía está en Outbox;
- hasta 20 mensajes de chats anteriores que aún no tengan resumen;
- límite global de 10000 caracteres para memoria entre chats.

Así un chat extenso no se carga completo en RAM ni se envía completo al modelo.

## Privacidad

El contexto se sanea antes de persistirse. Los logs de divergencia contienen ids y hashes, no mensajes, credenciales ni prompts completos.
