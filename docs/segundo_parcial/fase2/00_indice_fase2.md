# Fase 2 - Motor unico de IA con Ollama y Qwen

## Objetivo

Integrar un unico asistente adaptable que detecta una o varias intenciones, utiliza contexto autorizado del proyecto, consulta Ollama/Qwen mediante salida estructurada y conserva un fallback determinista seguro.

## Documentos

1. [Arquitectura del motor unico](01_arquitectura_motor_unico.md)
2. [Integracion con Ollama y Qwen](02_integracion_ollama_qwen.md)
3. [Clasificacion de intenciones](03_clasificacion_intenciones.md)
4. [Contexto y prompts](04_contexto_y_prompts.md)
5. [Acciones, seguridad y fallback](05_acciones_seguridad_fallback.md)
6. [Pruebas y evaluacion](06_pruebas_evaluacion.md)
7. [Resumen y cierre](07_resumen_fase2.md)

## Entregables principales

- Abstraccion `AiProvider` y proveedor asincrono `OllamaProvider`.
- Orquestador unico con clasificador multiintencion y fallback por reglas.
- Salidas JSON validadas con Pydantic y hasta dos reparaciones.
- Contexto por proyecto con presupuesto determinista y eliminacion de secretos.
- Persistencia idempotente de mensajes, acciones y recomendaciones.
- Confirmacion o rechazo de acciones tipadas con control de dependencias y version.
- Contratos REST y TypeScript para consumo del frontend.
- Dataset offline y pruebas sin dependencia de Ollama real.

## Estado

Fase terminada. Ollama no se encuentra instalado en la maquina de validacion; por ello la prueba real queda omitida de forma explicita. El proveedor, los errores y la reparacion se verificaron con `httpx.MockTransport`.
