# Plataforma CASE Inteligente

Plataforma CASE inteligente y colaborativa para modelado UML, validacion asistida por IA local offline y generacion automatica de software.

## Configuracion y publicacion


## Componentes

- `frontend/`: aplicacion web React + TypeScript + Vite + Tailwind.
- `backend/`: backend principal Python 3.12 + FastAPI.
- `ai-engine/`: estructura inicial del motor de IA local offline.
- `docs/`: documentacion del proyecto y avances por fase.

## Comandos base

Frontend:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

Backend:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

IA:

```powershell
cd ai-engine
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ai_engine.inference.health
```

