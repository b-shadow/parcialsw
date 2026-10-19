# Fase 7 - Integracion FastAPI y frontend

## Backend

Se agrego `backend/app/modules/generacion_software/routers/ai.py`.

Endpoints:

- `GET /api/v1/ai/profile`
- `POST /api/v1/ai/uml/text`
- `POST /api/v1/ai/uml/voice`
- `POST /api/v1/ai/uml/image`
- `POST /api/v1/ai/uml/validate`
- `POST /api/v1/ai/software/plan`

Todos los endpoints usan usuario autenticado.

## Servicio backend

Archivo:

- `backend/app/modules/generacion_software/services/ai_service.py`

Integra el paquete local:

```text
case-inteligente-ai-engine
```

## Frontend

Archivo:

- `frontend/src/modules/modelado_uml_inteligente/services/aiService.ts`

El editor UML consume endpoints de IA local y muestra motor, confianza y clases detectadas antes de persistir el diagrama generado.
