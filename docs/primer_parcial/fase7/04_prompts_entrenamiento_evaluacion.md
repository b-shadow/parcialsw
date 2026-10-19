# Fase 7 - Prompts, entrenamiento y evaluacion

## Prompts

Se crearon prompts especializados en:

- `ai_engine/prompts/uml_generation.md`
- `ai_engine/prompts/uml_validation.md`
- `ai_engine/prompts/software_generation.md`

## Estrategia de entrenamiento

Archivo:

- `ai_engine/training/dataset_strategy.py`

Dataset propuesto:

- Descripciones textuales UML.
- Diagramas XMI.
- Plantillas Spring Boot.
- Plantillas Flutter.

## Ajuste futuro

Se documenta compatibilidad con:

- LoRA.
- QLoRA.
- Fine tuning supervisado.

## Metricas

- Exactitud de clases.
- Exactitud de relaciones.
- Compilacion de codigo generado.
- Calidad de reconstruccion desde imagen.
