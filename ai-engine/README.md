# Motor IA local offline

Componente local de inteligencia artificial para la plataforma CASE inteligente.

## Objetivo

Ejecutar capacidades inteligentes sin depender de APIs externas en el producto final:

- Texto a UML.
- Voz a UML.
- Imagen a UML.
- Validacion UML.
- Apoyo a generacion Spring Boot y Flutter.

## Arquitectura

- `models/`: perfil del modelo local seleccionado.
- `inference/`: motor de inferencia determinista offline.
- `preprocessing/`: normalizacion de texto, voz e imagen.
- `prompts/`: prompts especializados para evolucion futura.
- `validators/`: validacion de calidad UML.
- `services/`: orquestacion publica del motor local.
- `training/`: estrategia de dataset, metricas y ajuste.
- `datasets/`: dataset semilla especializado en dominios academicos y empresariales.
- `embedding/`: recuperacion semantica local sin servicios externos.
- `evaluation/`: metricas offline de precision de clases y relaciones.

## Especializacion Fase 10

- Perfil principal: Qwen2.5-Coder-7B-Instruct cuantizado para produccion local.
- Perfil reducido: Qwen2.5-Coder-1.5B-Instruct cuantizado para equipos limitados.
- Runtime operativo: inferencia local con fallback determinista, sin llamadas de red.
- Entrenamiento previsto: SFT, LoRA, QLoRA y RAG local.
- Dataset inicial: casos biblioteca, ventas, academico e inventario.
- Tareas: generar UML, modificar UML, validar UML, recuperar conocimiento y guiar generacion Spring Boot/Flutter.

## Ejecucion de verificacion

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ai_engine.inference.health
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```
