# Dataset y Entrenamiento

## Dataset semilla

Se implemento dataset especializado en `ai_engine/datasets/software_cases.py`.

Incluye dominios:

- biblioteca.
- ventas.
- academico.
- inventario.

Cada registro contiene:

- intencion.
- prompt de entrada.
- clases esperadas.
- relaciones esperadas.
- artefactos objetivo.

## Entrenamiento

Se implemento `ai_engine/training/specialization.py` con plan de:

- normalizacion de requerimientos.
- etiquetado UML.
- pares UML a Spring Boot.
- pares UML a Flutter.
- evaluacion offline.

## Tecnicas

- SFT.
- LoRA.
- QLoRA.
- RAG local.

## Metricas

- precision de clases.
- precision de relaciones.
- compilacion backend.
- compilacion Flutter.
- calidad de validacion UML.
