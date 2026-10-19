# PROMPT FASE 3: IA COLABORATIVA Y MEMORIA COMPARTIDA POR PROYECTO

## 0. Instruccion maestra

Implementar la Fase 3 de la segunda parte de CASE Inteligente: convertir el motor unico de IA de la Fase 2 en una experiencia colaborativa compartida por proyecto, con identidad de usuario, memoria persistente, sincronizacion en tiempo real, acciones confirmables, recomendaciones, referencias y recuperacion segura tras reconexiones.

Esta fase debe utilizar exactamente:

- La persistencia y los contratos de la Fase 1.
- El orquestador, proveedores Ollama/Qwen, fallback, clasificacion multiintencion y politica de acciones de la Fase 2.
- La autenticacion, membresia, permisos, WebSocket, bitacora, versiones y notificaciones existentes.

No crear otra IA, otro historial ni un canal paralelo de permisos. Todos los colaboradores autorizados de un proyecto interactuan con una sola conversacion logica y una sola IA integral. La IA adapta su actuacion a cada solicitud; no tiene personalidades seleccionables.

---

## 1. Resultado funcional buscado

Al terminar:

1. Dos o mas usuarios del mismo proyecto ven la misma conversacion.
2. Cada mensaje identifica autor, fecha, estado y secuencia.
3. La IA conoce el proyecto, el usuario y el diagrama activo autorizado.
4. Los mensajes nuevos aparecen en tiempo real.
5. Una reconexion recupera eventos perdidos sin duplicarlos.
6. Las acciones muestran quien las solicito y su estado.
7. Confirmar, rechazar o aplicar una accion se refleja para todos.
8. Las recomendaciones quedan asociadas a elementos concretos.
9. El historial puede crecer sin enviar todo al modelo.
10. Revocar acceso desconecta al usuario e impide nuevas consultas.

---

## 2. Dependencias y precondiciones

No iniciar si no estan verificadas:

### Fase 1

- `AiProjectSettings`.
- `AiConversation` unica por proyecto.
- `AiMessage` con `sequence_number`, `client_message_id` y `correlation_id`.
- `AiAction` y estados.
- `AiRecommendation`.
- Contratos WebSocket version 2.
- Endpoints paginados de historial.

### Fase 2

- Proveedor Ollama.
- Proveedor de reglas.
- Orquestador unico.
- Clasificacion multiintencion.
- Construccion segura de contexto.
- Salida estructurada validada.
- Politica de riesgo y confirmacion.
- Endpoint idempotente de interaccion.

### Plataforma existente

- Autenticacion JWT.
- Roles de proyecto.
- `ConnectionManager`.
- `/ws/projects/{project_id}`.
- Eventos colaborativos persistentes.
- Desconexion por revocacion de acceso.
- Notificaciones Web Push.

Si alguna dependencia falta, completar primero su fase propietaria. No duplicarla dentro de esta fase.

---

## 3. Alcance exacto

- Conversacion visible y compartida por proyecto.
- Identidad confiable del autor.
- Historial paginado.
- Estados de procesamiento de IA.
- Difusion WebSocket posterior a persistencia.
- Reconexion y sincronizacion incremental.
- Presencia de colaboradores.
- Memoria de corto y largo plazo.
- Resumen estructurado de conversacion.
- Referencias a elementos del proyecto.
- Visualizacion de acciones y recomendaciones.
- Confirmacion y rechazo colaborativos con permisos.
- Notificaciones de eventos relevantes.
- UI de asistente dentro del contexto del proyecto.
- Pruebas concurrentes y multiusuario.

---

## 4. Fuera de alcance

- Personalidades de IA.
- Generacion final de Spring Boot/Flutter basada en metodos.
- Editor completo de especificacion de metodos.
- Editor de estilos terminado.
- PWA movil final.
- Edicion UML completa dentro del chat.
- Redis obligatorio o despliegue distribuido multiinstancia.
- Entrenamiento del modelo.

La fase debe dejar contratos consumibles por fases posteriores sin adelantar sus interfaces completas.

---

## 5. Herramientas

### Backend

- FastAPI REST y WebSocket.
- SQLAlchemy 2 y PostgreSQL.
- Pydantic 2.
- Servicios de IA de Fase 2.
- Pytest y soporte WebSocket de Starlette/FastAPI.
- `asyncio` para conexiones y emisiones.

### Frontend

- React y TypeScript.
- Cliente REST existente.
- Cliente WebSocket existente.
- Store local solo para cache de UI, nunca como fuente definitiva.
- Vitest y Testing Library.

### Tiempo real

Mantener WebSocket nativo. No introducir Socket.IO si el sistema ya funciona con WebSocket nativo.

---

## 6. Principio de consistencia

Los comandos de negocio se envian por REST:

```text
Cliente
  -> POST interaccion/confirmacion/rechazo
  -> backend autentica y valida
  -> backend persiste
  -> backend confirma transaccion
  -> backend emite evento WebSocket
  -> todos los clientes actualizan su estado
```

WebSocket se usa para:

- Difusion de resultados persistidos.
- Presencia.
- Estado efimero de procesamiento.
- Heartbeat.
- Aviso de resincronizacion.

No enviar comandos mutantes exclusivamente por WebSocket. Esto evita saltar validacion, idempotencia, auditoria y manejo HTTP de errores.

---

## 7. Arquitectura requerida

```text
ProjectAssistantPanel
  -> projectAiService (REST)
  -> projectSocket (eventos)

FastAPI Project AI Router
  -> ProjectAiCollaborationService
      -> permisos
      -> ConversationRepository
      -> UnifiedAiOrchestrator
      -> ActionService
      -> RecommendationService
      -> DomainEventPublisher
          -> ConnectionManager
          -> PushNotificationService
```

El orquestador no conoce WebSocket. El publicador no decide reglas de negocio. El frontend no genera secuencias del servidor.

---

## 8. Flujo de una consulta

1. El usuario escribe desde un proyecto.
2. El cliente genera `client_message_id` UUID.
3. Envia REST con proyecto, diagrama activo y version base.
4. Backend obtiene usuario desde JWT.
5. Verifica membresia y permisos.
6. Resuelve idempotencia.
7. Persiste mensaje de usuario.
8. Confirma la transaccion.
9. Emite `AI_MESSAGE_CREATED`.
10. Emite estado efimero `AI_PROCESSING_STARTED`.
11. Construye contexto y llama Fase 2 sin transaccion abierta.
12. Persiste respuesta, acciones y recomendaciones en una nueva transaccion.
13. Emite eventos persistidos en orden.
14. Emite `AI_PROCESSING_FINISHED`.
15. Responde REST con el resultado final.

Si el cliente se desconecta, el procesamiento puede terminar y quedar persistido. Al reconectar, debe recuperar el resultado.

---

## 9. Identidad

- Autor obtenido exclusivamente del JWT.
- `user_id` enviado por cliente se ignora o rechaza.
- Guardar UUID y mostrar nombre resuelto por backend.
- Conservar autor aunque cambie su nombre posteriormente mediante snapshot de display name si el modelo lo requiere.
- Mensajes del asistente tienen `role=assistant` y autor de usuario nulo.
- Acciones guardan `requested_by_user_id`.
- Confirmaciones guardan `confirmed_by_user_id`.
- La IA recibe rol y permisos efectivos, no afirmaciones textuales.

---

## 10. Conversacion unica

- Una conversacion principal por proyecto.
- Creacion perezosa y concurrentemente segura.
- No crear conversaciones por usuario.
- No reiniciar al cerrar navegador.
- No borrar al restaurar una version.
- Archivar solo mediante futura politica administrativa.
- El orden se define por `sequence_number`, no por hora del cliente.

La conversacion representa memoria comunicacional; el snapshot representa estado restaurable. Son conceptos separados.

---

## 11. Historial paginado

Endpoints de Fase 1:

- Obtener ultimos mensajes con limite.
- Obtener mensajes anteriores a una secuencia.
- Obtener mensajes posteriores a una secuencia.

Reglas:

- Cursor por secuencia.
- Limite predeterminado moderado y maximo estricto.
- Orden estable.
- No offset.
- Respuesta informa `has_more_before`, `has_more_after`, secuencia minima y maxima.
- Cargar historial antiguo al desplazar hacia arriba.
- No descargar toda la conversacion al abrir.

---

## 12. Protocolo WebSocket

Extender el sobre version 2 definido en Fase 1.

Eventos persistentes:

- `AI_MESSAGE_CREATED`
- `AI_MESSAGE_STATUS_CHANGED`
- `AI_ACTION_PROPOSED`
- `AI_ACTION_STATUS_CHANGED`
- `AI_RECOMMENDATION_CREATED`
- `AI_RECOMMENDATION_STATUS_CHANGED`
- `AI_CONVERSATION_SUMMARY_UPDATED`

Eventos efimeros:

- `AI_PROCESSING_STARTED`
- `AI_PROCESSING_FINISHED`
- `AI_PROCESSING_FAILED`
- `PRESENCE_JOINED`
- `PRESENCE_LEFT`
- `PRESENCE_SNAPSHOT`
- `SYNC_REQUIRED`

Todo evento persistente incluye:

- `protocol_version`.
- `event_id`.
- `project_id`.
- `sequence_number` del evento de proyecto si aplica.
- `conversation_sequence` para mensajes.
- `correlation_id`.
- `occurred_at` del servidor.
- Actor.
- Payload tipado.

No usar hora local para ordenar.

---

## 13. Secuencias

Mantener dos conceptos:

1. `conversation_sequence`: orden del mensaje en la conversacion.
2. `project_event_sequence`: orden global de eventos persistidos del proyecto.

No asumir que son iguales.

El frontend deduplica mensajes por ID y eventos por `event_id`. Usa secuencias para detectar huecos.

Si recibe secuencia 108 y esperaba 106, solicita sincronizacion desde 105 antes de continuar o marca `SYNC_REQUIRED`.

---

## 14. Publicacion posterior al commit

No emitir eventos antes de confirmar la transaccion.

Implementar un publicador de dominio que reciba DTO serializable. Si no existe outbox transaccional, cumplir como minimo:

1. Persistir y confirmar.
2. Intentar broadcast.
3. Si broadcast falla, mantener dato persistido.
4. Clientes recuperan mediante catch-up.

Documentar que el WebSocket es at-least-once desde la perspectiva del cliente y exigir deduplicacion.

No hacer rollback de negocio porque un socket se desconecto.

---

## 15. Reconexion y catch-up

Al conectar:

- Autenticar origen, token, usuario activo y membresia.
- Asignar `connection_id` UUID.
- Recibir opcionalmente `last_project_sequence` y `last_conversation_sequence` mediante mensaje inicial o REST.
- Enviar `SESSION_CONNECTED` con secuencias actuales.
- Si existe hueco, enviar `SYNC_REQUIRED`.

Cliente:

- Usa backoff exponencial con jitter.
- No crea mas de una conexion activa por vista.
- Cancela timers al desmontar.
- Tras reconectar consulta mensajes posteriores.
- Deduplica resultados recibidos por REST y socket.

No retransmitir comandos REST automaticamente sin clave idempotente.

---

## 16. Presencia

Extender `ConnectionManager` con metadata:

- `connection_id`.
- `user_id`.
- `display_name`.
- `project_role`.
- `connected_at`.
- `last_seen_at`.
- `active_diagram_id` opcional.
- Cantidad de conexiones por usuario.

Reglas:

- Un usuario con dos pestanas aparece una sola vez con contador interno.
- Emitir `PRESENCE_LEFT` solo al cerrar su ultima conexion.
- No persistir cada heartbeat.
- Heartbeat revalida sesion y membresia.
- Revocar acceso cierra todas sus conexiones.
- Limitar conexiones por proyecto y por usuario.
- No exponer correo si no es necesario.

---

## 17. Estado de procesamiento

Mostrar:

- Quien realizo la consulta.
- Que la IA esta procesando.
- Correlation ID interno.
- Inicio y finalizacion.
- Error recuperable.

No mostrar razonamiento interno del modelo.

No persistir cada indicador efimero. Persistir solamente estados importantes del mensaje (`pending`, `completed`, `failed`).

Evitar multiples indicadores para el mismo correlation ID.

---

## 18. Memoria de corto plazo

Para cada inferencia incluir:

- Solicitud actual.
- Resumen persistido.
- Mensajes posteriores al limite resumido.
- Mensajes referenciados expresamente.
- Diagrama activo autorizado.
- Acciones pendientes relacionadas.

Respetar el presupuesto de Fase 2. No pasar todo el historial.

---

## 19. Memoria de largo plazo y resumen

Usar campos de Fase 1:

- `summary`.
- `summary_until_sequence`.
- `last_message_sequence`.

Disparador:

- Cuando mensajes no resumidos superen `summary_trigger_messages`.
- Nunca en cada mensaje.
- Una sola tarea de resumen por conversacion.

El resumen estructurado debe contener:

```json
{
  "project_goal": "...",
  "decisions": [],
  "open_questions": [],
  "recent_changes": [],
  "important_entities": [],
  "pending_actions": [],
  "member_preferences_relevant_to_work": [],
  "summary_until_sequence": 40
}
```

No incluir secretos, informacion personal irrelevante o instrucciones privilegiadas aportadas por usuarios.

El resumen no reemplaza ni elimina mensajes originales. Actualizar solo si la secuencia resumida no fue procesada por otro worker.

---

## 20. Estrategia de resumen

1. Tomar resumen anterior.
2. Tomar mensajes completados desde `summary_until_sequence + 1` hasta un limite estable.
3. Solicitar resumen estructurado al motor de Fase 2.
4. Validar JSON.
5. Aplicar sanitizacion.
6. Actualizar resumen y frontera en transaccion con bloqueo.
7. Emitir `AI_CONVERSATION_SUMMARY_UPDATED` sin difundir contenido sensible completo.

Fallback:

- Si Ollama no esta disponible, usar resumen determinista por eventos o aplazar.
- No bloquear la respuesta principal por fallo de resumen.
- Registrar fallo sin duplicar tareas infinitas.

---

## 21. Referencias

Los mensajes, acciones y recomendaciones pueden referenciar:

- Proyecto.
- Diagrama.
- Clase.
- Atributo.
- Metodo.
- Relacion.
- Version.
- Generacion.
- Mensaje anterior.

Cada referencia contiene tipo, ID, etiqueta y estado opcional.

Backend valida:

- Existencia.
- Pertenencia al proyecto.
- Visibilidad para el usuario.

Frontend permite navegar a la referencia sin confiar en rutas entregadas por la IA. Construye rutas desde tipo e ID conocidos.

---

## 22. Acciones colaborativas

Una tarjeta de accion muestra:

- Quien la solicito.
- Tipo y descripcion.
- Objetivos afectados.
- Riesgo.
- Dependencias.
- Confirmacion requerida.
- Estado.
- Usuario que confirmo o rechazo.
- Resultado o error.

Transiciones permitidas segun Fase 2. El frontend no cambia estado de forma definitiva antes de respuesta del servidor.

Si dos usuarios confirman simultaneamente:

- Bloquear o actualizar condicionalmente por estado.
- Una transicion gana.
- La otra recibe estado actual sin segunda ejecucion.

---

## 23. Permisos de acciones

- Leer conversacion: miembro activo.
- Preguntar: miembro activo.
- Proponer cambio: segun permiso de edicion.
- Confirmar cambio UML: permiso de edicion.
- Rechazar propuesta: solicitante, editor autorizado u organizador segun politica.
- Restaurar version: solo organizador o creador.
- Cambiar configuracion IA: organizador o creador.

La IA puede recomendar cualquier mejora permitida por contexto, pero no eleva permisos.

---

## 24. Recomendaciones colaborativas

Mostrar recomendaciones separadas de mensajes normales cuando tengan ciclo de vida.

Permitir:

- Abrir referencia.
- Aceptar.
- Descartar con nota opcional.
- Marcar resuelta.

Actualizar estado por REST y emitir evento posterior al commit.

No convertir automaticamente una recomendacion aceptada en accion aplicada; debe crear o vincular una accion validada.

---

## 25. Notificaciones

Enviar Push solo para eventos relevantes:

- Mencion directa futura, si se implementa.
- Recomendacion critica.
- Accion de alto riesgo pendiente de confirmacion.
- Accion aplicada que modifica significativamente el proyecto.
- Fallo de una accion solicitada por el usuario.

Reglas:

- Excluir al actor cuando ya conoce el evento.
- No enviar push por cada token, mensaje propio o presencia.
- Agrupar por proyecto y tipo mediante `tag`.
- URL apunta al proyecto y, si es posible, al mensaje o accion.
- Fallo Push no revierte la operacion.

---

## 26. UI del asistente de proyecto

Crear un panel o ventana accesible dentro del proyecto.

No confundir con `AssistantWidget` global de manual de usuario. El manual puede mantenerse para ayuda general; el asistente de proyecto utiliza contexto, memoria y acciones reales.

Componentes sugeridos:

```text
ProjectAiAssistant
  ConversationHeader
  PresenceList
  MessageTimeline
  MessageBubble
  ReferenceChips
  ActionCard
  RecommendationCard
  ProcessingIndicator
  Composer
```

Estados:

- Cargando historial.
- Sin mensajes.
- Enviando.
- Procesando.
- Esperando confirmacion.
- Reconectando.
- Sin Ollama con fallback.
- Error recuperable.
- Acceso revocado.

No colocar tarjetas dentro de tarjetas. Mantener dimensiones responsive y textos sin overflow.

---

## 27. Compositor de mensajes

- Texto multilinea.
- Envio deshabilitado si vacio o excede limite.
- Conserva borrador local por proyecto.
- Permite asociar diagrama activo.
- Muestra claramente si una accion necesitara confirmacion.
- Enter envia solo segun convencion accesible; Shift+Enter crea linea.
- Evita doble envio mientras se procesa el mismo ID.
- Genera UUID idempotente antes de REST.
- Ante timeout, permite reintentar con el mismo ID.

No permitir que el usuario elija una personalidad.

---

## 28. Timeline

- Orden por secuencia.
- Nombre y hora del servidor.
- Diferenciar usuario, IA, sistema y herramienta sin depender solo de color.
- Renderizar texto como contenido seguro.
- Referencias con botones conocidos.
- Acciones y recomendaciones vinculadas.
- Cargar mensajes antiguos sin saltar posicion.
- En nuevos mensajes, auto-scroll solo si el usuario esta cerca del final.
- Indicador de mensajes nuevos si esta leyendo historial.

---

## 29. Estado frontend

Fuente definitiva: backend.

Store por proyecto:

- Mensajes indexados por ID.
- Orden de IDs por secuencia.
- Acciones indexadas.
- Recomendaciones indexadas.
- Presencia efimera.
- Secuencias conocidas.
- Estado de conexion.
- Procesamientos por correlation ID.

Reducers/event handlers deben ser idempotentes. Un mensaje recibido primero por REST y despues por WebSocket se fusiona, no se duplica.

---

## 30. Cliente WebSocket

Extender `projectSocket.ts` sin romper eventos UML.

Requisitos:

- Union discriminada para eventos.
- Parser defensivo.
- Compatibilidad version 1 y 2.
- Backoff exponencial con jitter.
- Heartbeat.
- Estado observable.
- Deduplicacion.
- Catch-up tras huecos.
- Limpieza completa al salir del proyecto.
- Cambio de token fuerza reconexion.

No usar `any`. No cerrar el socket por evento nuevo desconocido.

---

## 31. ConnectionManager

Fortalecer sin convertirlo en repositorio:

- Metadata de conexiones.
- Limite por usuario y proyecto.
- Broadcast concurrente con locks existentes.
- Timeout de envio.
- Limpieza de conexiones fallidas.
- Presencia agregada por usuario.
- Desconexion por revocacion.
- Metodos para enviar a un usuario y excluir actor.

No guardar historial dentro de memoria del manager.

Documentar que el manager en memoria sirve para una instancia. Crear interfaz de bus/publicador para poder sustituirlo en despliegue multiinstancia sin reescribir servicios. No agregar Redis sin requerimiento operativo y pruebas.

---

## 32. Rate limiting y abuso

- Limite de mensajes IA por usuario y ventana.
- Limite simultaneo de inferencias por usuario/proyecto.
- Limite de conexiones.
- Limite de bytes por evento.
- Limite de confirmaciones repetidas.
- Mensajes demasiado largos reciben 422 o 413 coherente.
- Heartbeats no cuentan como mensajes de IA.

No mantener contadores solamente en frontend.

---

## 33. Privacidad y seguridad

- Conversacion visible solo a miembros activos.
- Revalidar membresia en heartbeat y mutaciones.
- No exponer correos innecesarios.
- No enviar tokens en query string si existe subprotocolo seguro actual.
- Validar Origin.
- Escapar contenido.
- No incluir prompts internos o pensamiento del modelo.
- No incluir conversaciones en snapshots.
- No registrar contenido completo en logs.
- Limitar referencias y metadatos.
- Cerrar sockets al revocar usuario.

---

## 34. Manejo de errores

Estados distinguibles:

- Sin conexion WebSocket.
- REST no disponible.
- Ollama no disponible con fallback.
- Inferencia fallida.
- Mensaje rechazado.
- Conflicto de version.
- Accion ya procesada.
- Permiso revocado.
- Hueco de sincronizacion.

Un fallo de broadcast no cambia un mensaje completado a fallido. Un fallo de inferencia si actualiza el mensaje correspondiente y emite evento de estado.

---

## 35. Observabilidad

Registrar sin contenido sensible:

- Project ID.
- User ID.
- Connection ID.
- Correlation ID.
- Event ID.
- Secuencias.
- Tipo de evento.
- Latencia REST, IA y broadcast.
- Reintentos y reconexiones.
- Numero de conexiones.
- Uso de fallback.
- Errores tipados.

Metricas deseables:

- Conexiones activas.
- Mensajes por minuto.
- Latencia de respuesta IA.
- Reconexiones.
- Huecos recuperados.
- Eventos duplicados descartados.
- Acciones propuestas, confirmadas, rechazadas y fallidas.

---

## 36. Pruebas backend unitarias

### Conversacion

- Una por proyecto.
- Autor correcto.
- Secuencia estable.
- Idempotencia.
- Paginacion.
- Aislamiento.

### Resumen

- Disparador por umbral.
- Incluye solo mensajes no resumidos.
- Actualiza frontera.
- Dos tareas no pisan resumen.
- Fallo no afecta mensaje principal.
- Salida invalida no se guarda.

### Acciones

- Transiciones validas.
- Doble confirmacion no duplica ejecucion.
- Permisos.
- Conflicto de version.
- Rollback coherente.

### Eventos

- DTO version 2 correcto.
- Emision posterior al commit.
- Actor y correlacion.
- Payload sin secretos.

### Presencia

- Dos pestanas, un usuario visible.
- Ultima pestana emite salida.
- Revocacion desconecta todas.
- Limites.

---

## 37. Pruebas WebSocket multiusuario

Con dos clientes autenticados:

1. Ambos conectan al mismo proyecto.
2. Reciben snapshot de presencia.
3. Usuario A envia interaccion REST.
4. Usuario B recibe mensaje y estado.
5. A recibe respuesta REST y evento sin duplicar.
6. B confirma accion autorizada.
7. Ambos ven el nuevo estado.

Probar ademas:

- Proyectos diferentes no comparten eventos.
- Usuario no miembro es rechazado.
- Token expirado cierra conexion.
- Evento grande es rechazado.
- Rate limit cierra o rechaza apropiadamente.
- Cliente lento no bloquea a los demas.
- Reconectar recupera mensajes omitidos.
- Evento duplicado se ignora.
- Hueco de secuencia activa catch-up.

---

## 38. Pruebas frontend

- Timeline ordena por secuencia.
- REST + WebSocket no duplican.
- Historial antiguo conserva scroll.
- Estado de procesamiento aparece y desaparece.
- Reconexion cambia indicador.
- Catch-up inserta faltantes.
- Accion muestra riesgo y confirmacion.
- Doble clic no confirma dos veces.
- Recomendacion cambia de estado.
- Referencia navega mediante ruta controlada.
- Texto no ejecuta HTML.
- Vista estrecha no desborda.
- Componentes accesibles por teclado.

---

## 39. Pruebas de memoria

Crear una conversacion larga y verificar:

- No se envia todo al modelo.
- El resumen conserva decisiones.
- Preguntas abiertas permanecen.
- Mensajes posteriores se incluyen.
- Referencias relevantes se conservan.
- Informacion obsoleta puede marcarse como reemplazada.
- No se inventan decisiones.
- Mensajes originales permanecen consultables.

---

## 40. Casos de aceptacion

### Dos usuarios

A pregunta "Conviene separar Factura de Venta?". B observa pregunta, procesamiento y respuesta con autor correcto.

### Solicitud de cambio

A solicita relacion uno a uno. Ambos ven propuesta. B con permiso confirma. El cambio se aplica una vez y ambos reciben resultado.

### Usuario sin permiso

Un visor puede preguntar y leer, pero no confirmar una modificacion.

### Reconexion

B pierde red mientras se generan dos mensajes. Al reconectar recupera ambos en orden sin duplicados.

### Conversacion extensa

Tras superar el umbral, se actualiza resumen. Una nueva pregunta mantiene decisiones previas sin cargar todo el historial.

### Revocacion

El organizador elimina a B. Sus sockets se cierran y las rutas devuelven acceso denegado.

### Accion simultanea

A y B confirman al mismo tiempo. Solo una ejecucion ocurre; ambos ven el mismo estado final.

---

## 41. Compatibilidad

- Eventos UML actuales siguen funcionando.
- Historial colaborativo y versiones siguen disponibles.
- El asistente manual global no se elimina sin reemplazo.
- Los endpoints legacy IA siguen operativos.
- Un proyecto antiguo crea conversacion al primer uso.
- Sin Ollama se informa fallback.
- Sin WebSocket, REST e historial siguen siendo utilizables tras recargar.

---

## 42. Orden obligatorio de implementacion

1. Verificar Fases 1 y 2.
2. Disenar publicador posterior al commit.
3. Extender contratos de eventos.
4. Fortalecer ConnectionManager y presencia.
5. Implementar flujo REST-persistencia-broadcast.
6. Implementar catch-up y secuencias.
7. Implementar memoria corta.
8. Implementar resumen de largo plazo.
9. Integrar acciones y recomendaciones.
10. Integrar notificaciones relevantes.
11. Extender cliente WebSocket.
12. Implementar store idempotente.
13. Construir panel del asistente.
14. Agregar pruebas multiusuario.
15. Probar reconexion, huecos y revocacion.
16. Ejecutar suites completas.
17. Documentar comportamiento real.

---

## 43. Comandos de verificacion

```powershell
cd ai-engine
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check app tests migrations
```

```powershell
cd frontend
npm run lint
npm run test -- --run
npm run build
```

Realizar prueba manual con dos navegadores o perfiles de navegador diferentes y dos usuarios reales.

---

## 44. Documentacion a producir

```text
docs/segundo_parcial/fase3/
    00_indice_fase3.md
    01_arquitectura_colaborativa_ia.md
    02_protocolo_websocket.md
    03_memoria_resumen_contexto.md
    04_acciones_recomendaciones.md
    05_interfaz_asistente_proyecto.md
    06_pruebas_multiusuario.md
    07_resumen_fase3.md
```

Incluir diagramas Mermaid de flujo REST/WebSocket, secuencias de reconexion y memoria.

---

## 45. Entregables

- Servicio colaborativo de IA.
- Publicador de eventos.
- ConnectionManager reforzado.
- Presencia.
- Catch-up y reconexion.
- Resumen de memoria.
- Endpoints de acciones/recomendaciones necesarios.
- Cliente WebSocket tipado.
- Store idempotente.
- Panel de asistente de proyecto.
- Notificaciones relevantes.
- Pruebas backend, WebSocket y frontend.
- Documentacion.

---

## 46. Prohibiciones

- No crear personalidades.
- No usar WebSocket para saltar REST y permisos.
- No emitir antes del commit.
- No guardar historial en memoria del socket.
- No ordenar por reloj del cliente.
- No duplicar mensajes recibidos por dos canales.
- No resumir eliminando mensajes.
- No incluir conversacion en versiones.
- No exponer razonamiento interno.
- No ejecutar HTML del chat.
- No enviar push por cada evento menor.
- No afirmar soporte multiinstancia con manager en memoria.
- No introducir Redis sin necesidad y pruebas.
- No permitir confirmacion sin permiso.
- No dejar acciones en ejecucion indefinida.

---

## 47. Lista final

- [ ] Fases 1 y 2 verificadas.
- [ ] Conversacion unica por proyecto.
- [ ] Identidad desde JWT.
- [ ] REST persiste antes de broadcast.
- [ ] Eventos versionados y tipados.
- [ ] Secuencias y deduplicacion.
- [ ] Reconexion con catch-up.
- [ ] Presencia agregada por usuario.
- [ ] Memoria corta acotada.
- [ ] Resumen largo validado.
- [ ] Acciones sincronizadas.
- [ ] Recomendaciones sincronizadas.
- [ ] Permisos probados.
- [ ] Revocacion desconecta.
- [ ] Push solo para eventos relevantes.
- [ ] UI responsive y accesible.
- [ ] Pruebas multiusuario aprobadas.
- [ ] Endpoints UML anteriores intactos.
- [ ] Sin secretos ni logs sensibles.

---

## 48. Informe final requerido

Reportar:

1. Arquitectura implementada.
2. Eventos y endpoints agregados.
3. Estrategia de secuencias e idempotencia.
4. Estrategia de memoria y resumen.
5. Permisos de acciones.
6. Comportamiento de reconexion.
7. Limites de instancia unica o soporte distribuido real.
8. Pruebas multiusuario y resultados exactos.
9. Limitaciones que pasan a Fase 4.

---

## 49. Resultado final esperado

CASE Inteligente debe ofrecer una IA realmente compartida por proyecto. Cada colaborador autorizado puede conversar con el mismo asistente, observar mensajes y acciones en tiempo real, reconocer quien hizo cada solicitud, recuperar el historial tras desconectarse y mantener continuidad mediante resumen de memoria.

La experiencia debe ser consistente incluso cuando REST y WebSocket entreguen el mismo dato, cuando dos usuarios actuen simultaneamente o cuando Ollama no este disponible. La Fase 4 podra usar esta conversacion y el motor ya sincronizado para capturar especificaciones funcionales de metodos sin redisenar la colaboracion.
