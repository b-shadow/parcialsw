# Acciones, seguridad y fallback

## Catalogo cerrado

El esquema admite creacion, actualizacion y eliminacion de clases, atributos, metodos y relaciones; especificacion de metodos; guardado de version; y preparacion de generacion backend o Flutter. Pydantic rechaza cualquier tipo fuera del catalogo.

## Validacion del plan

Antes de persistir:

- Se validan payloads tipados.
- Se comprueba que el diagrama sea el activo.
- Se rechazan IDs y nombres externos al contexto.
- Se permiten referencias a clases creadas dentro del mismo plan.
- Se verifican dependencias existentes.
- Se detectan ciclos.
- Se ordenan las acciones.
- Se recalcula riesgo y confirmacion en codigo confiable.

Creaciones y actualizaciones son de riesgo medio. Eliminaciones son de riesgo alto y siempre requieren confirmacion.

## Persistencia e idempotencia

El endpoint principal usa `client_message_id`. Un reintento devuelve la respuesta ya persistida; si la primera solicitud sigue en proceso, devuelve conflicto y no inicia una segunda inferencia. El `correlation_id` es comun a solicitud y respuesta.

## Confirmacion

```text
POST /projects/{project_id}/ai/actions/{action_id}/confirm
POST /projects/{project_id}/ai/actions/{action_id}/reject
```

Confirmar ejecuta la accion; no existe un endpoint publico separado. Antes de ejecutar se vuelven a validar membresia, dependencias, estado y version base. El ejecutor llama exclusivamente servicios UML, especificaciones y versiones ya existentes.

Los planes se confirman accion por accion. Una dependencia debe estar `applied` antes de su sucesora. Este comportamiento declara exito parcial de forma explicita: cada accion posee estado y resultado propios. Un fallo pasa a `failed`, conserva un mensaje controlado y no deja `executing` abandonado.

## Fallback

`RuleEngineProvider` envuelve las capacidades previas de `LocalAIEngine` y agrega planes seguros para revision UML, creacion de clases/relaciones, eliminacion confirmable, especificacion de metodos y preparacion de generadores.

Si una solicitud no esta cubierta, informa la limitacion; no inventa que realizo el cambio. Si Ollama falla, los metadatos conservan el codigo de error y marcan `fallback_used`.

## Observabilidad

El backend registra IDs, proveedor, modelo, intenciones, duraciones, tokens, reintentos, fallback y cantidades. No registra prompt, contenido completo, JWT, claves ni imagenes base64.
