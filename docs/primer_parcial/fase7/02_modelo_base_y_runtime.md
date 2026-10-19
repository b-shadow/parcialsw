# Fase 7 - Modelo base y runtime

## Modelo seleccionado

Nombre:

```text
CASE-UML-Local-RuleModel-v1
```

## Motivo

- Funciona completamente offline.
- Requiere bajo consumo de memoria.
- Ejecuta en CPU.
- Produce salidas estructuradas.
- Es reemplazable por Llama, Mistral, Qwen o DeepSeek local en fases posteriores sin cambiar contratos.

## Runtime

```text
python-rule-engine
```

## Perfil

Endpoint:

```text
GET /api/v1/ai/profile
```

Devuelve:

- Modelo seleccionado.
- Runtime.
- Estado offline.
- Perfil de memoria.
- Politica de licencia.
- Tareas soportadas.
