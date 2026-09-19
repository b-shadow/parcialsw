# Modelos y Runtime Offline

## Seleccion de modelos

Modelo principal definido:

- `Qwen2.5-Coder-7B-Instruct cuantizado`

Modelo reducido:

- `Qwen2.5-Coder-1.5B-Instruct cuantizado`

## Criterios

- Buen desempeno en codigo.
- Soporte razonable para espanol.
- Capacidad para instrucciones tecnicas.
- Compatibilidad con ejecucion cuantizada.
- Uso local sin dependencia de APIs comerciales.

## Runtime

Runtime definido:

- `llama.cpp` u Ollama local para modelos cuantizados.
- fallback determinista `python-rule-engine` para ambientes academicos o equipos limitados.
- RAG local con vector store embebido.

## Politica offline

El producto final ejecuta inferencia sin red. Internet solo puede usarse en investigacion, comparacion o construccion controlada de datasets.
