# Arquitectura IA Especializada

## Alcance

La fase 10 profundiza el componente `ai-engine` como motor local offline especializado en ingenieria de software. La ejecucion final no depende de APIs externas.

## Modulos implementados

- `datasets`: dataset semilla con casos de biblioteca, ventas, academico e inventario.
- `embedding`: vector store local con busqueda semantica por similitud coseno.
- `evaluation`: metricas offline de precision de clases y relaciones.
- `training`: plan de especializacion con SFT, LoRA, QLoRA y RAG local.
- `inference`: motor que combina reglas deterministas, dataset especializado y conocimiento recuperado.
- `services`: fachada estable consumida por FastAPI.

## Capacidades

- Texto a UML con contexto RAG.
- Voz a UML desde transcripcion local.
- Imagen a UML desde descripcion/OCR local preparado.
- Validacion UML.
- Modificacion inteligente de UML.
- Busqueda de conocimiento local.
- Evaluacion offline.
- Guia de generacion Spring Boot y Flutter.

## Principio de arquitectura

La IA opera como componente independiente. FastAPI solo adapta contratos HTTP y conserva autenticacion, auditoria y seguridad de la plataforma.
