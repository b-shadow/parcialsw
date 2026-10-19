# Fase 7 - Arquitectura IA local

## Objetivo

Implementar un motor IA independiente, local y offline, integrado con FastAPI y el editor UML.

## Estructura implementada

```text
ai-engine/ai_engine/
  models/
  inference/
  preprocessing/
  prompts/
  services/
  training/
  validators/
```

## Capas

- `models`: perfil del modelo seleccionado.
- `inference`: motor local de inferencia.
- `preprocessing`: normalizacion de texto, voz e imagen.
- `prompts`: plantillas especializadas.
- `validators`: evaluacion de calidad UML.
- `services`: fachada publica del motor.
- `training`: estrategia de dataset, metricas y ajuste.

## Decision tecnica

Se implemento un motor local determinista basado en reglas de dominio como primera version offline ejecutable. No usa APIs externas ni llamadas de red durante inferencia.
