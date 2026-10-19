# Fase 1 - Arquitectura inicial de IA

## Principio rector

La IA del producto final debe ejecutarse localmente y offline. No se permite depender de APIs externas para el funcionamiento operativo.

## Capacidades previstas

- Texto a UML.
- Voz a UML.
- Imagen a UML.
- Validacion UML.
- Apoyo a transformacion de modelos.
- Apoyo a generacion de codigo Spring Boot y Flutter.

## Estructura inicial

```text
ai-engine/
|-- models/
|-- training/
|-- inference/
|-- datasets/
|-- preprocessing/
|-- prompts/
|-- validators/
`-- services/
```

## Modelos candidatos

- Llama.
- Mistral.
- Qwen.
- DeepSeek.

## Motores candidatos

- Ollama.
- llama.cpp.
- Transformers.

## Decision de Fase 1

La fase deja preparado el contrato tecnico y la estructura independiente. La seleccion final del modelo, cuantizacion, dataset y entrenamiento queda para las fases especializadas de IA.

