# Integracion FastAPI y Frontend

## Endpoints FastAPI

Se agregaron contratos:

- `POST /api/v1/ai/generate-uml`
- `POST /api/v1/ai/analyze-image`
- `POST /api/v1/ai/validate-model`
- `POST /api/v1/ai/uml/modify`
- `POST /api/v1/ai/generate-code`
- `POST /api/v1/ai/knowledge/search`
- `GET /api/v1/ai/dataset/summary`
- `GET /api/v1/ai/training/plan`
- `GET /api/v1/ai/evaluation/offline`

## Frontend React

Se extendio `aiService.ts` para consumir:

- validacion IA.
- modificacion UML.
- busqueda de conocimiento.
- evaluacion offline.

## Compatibilidad

Los endpoints de fase 7 se conservan. Los nuevos endpoints agregan alias y capacidades especializadas sin romper contratos anteriores.
