# Integracion con Ollama y Qwen

## Configuracion

Variables disponibles en `backend/.env.example`:

```text
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b
OLLAMA_SMALL_MODEL=qwen2.5-coder:1.5b
OLLAMA_CONNECT_TIMEOUT_SECONDS=3
OLLAMA_READ_TIMEOUT_SECONDS=120
OLLAMA_KEEP_ALIVE=10m
AI_MAX_RETRIES=2
AI_MAX_INPUT_CHARS=12000
AI_MAX_CONTEXT_CHARS=50000
AI_TEMPERATURE=0
AI_RULE_FALLBACK_ENABLED=true
AI_MAX_CONCURRENT_REQUESTS=2
```

El modelo efectivo puede configurarse por proyecto mediante `AiProjectSettings.model_name`. La URL de Ollama no puede modificarse desde una solicitud ni desde la configuracion del proyecto.

## Protocolo

`OllamaProvider` utiliza:

- `GET /api/tags` para salud y modelos instalados.
- `POST /api/chat` para inferencia.
- `stream: false` para recibir el plan completo.
- `format` con `UnifiedAiResult.model_json_schema()`.
- `temperature: 0`, limite de salida y `keep_alive` configurables.
- Metricas `prompt_eval_count`, `eval_count` y `done_reason`.

La respuesta se procesa con `StructuredOutputValidator`. Si no cumple el esquema, el proveedor agrega una instruccion breve de reparacion y reintenta como maximo dos veces. Nunca intenta descargar un modelo.

## Salud

`GET /api/v1/projects/{project_id}/ai/provider-health` devuelve disponibilidad, modelos instalados, modelo seleccionado, latencia y codigo de error. La consulta tiene cache breve para evitar llamadas repetidas a `/api/tags`.

## Errores tipados

- `provider_unavailable`
- `model_not_installed`
- `provider_timeout`
- `invalid_structured_output`
- `provider_protocol_error`
- `context_too_large`

Cuando el fallback esta deshabilitado, estas condiciones se traducen a HTTP 503 con codigo estable y sin traza interna. Cuando esta habilitado, se persiste el resultado determinista con `fallback_used=true` y una advertencia.

## Seguridad de red

Solo se aceptan URLs HTTP hacia `localhost`, `127.0.0.1` o `::1`, sin credenciales, ruta, query ni fragmento. El cliente no sigue redirecciones, limita tiempo, tamano de respuesta, reintentos y concurrencia.

## Runtime validado

En la maquina de cierre no se encontro el ejecutable `ollama`. La suite normal no lo requiere: simula ambos endpoints con transporte HTTP realista. Existe una prueba opcional que se omite cuando el runtime no esta instalado.
