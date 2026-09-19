# Fase 1 - Configuracion inicial del entorno

## Requisitos locales verificados

- Node.js disponible: `v22.19.0`.
- npm disponible: `10.9.3`.
- Python 3.12 disponible mediante `py -3.12`.

## Frontend

Archivos de configuracion:

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tailwind.config.js`
- `frontend/postcss.config.js`
- `frontend/.env.example`

Comandos:

```powershell
cd frontend
npm install
npm run build
npm run dev
```

## Backend

Archivos de configuracion:

- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/app/main.py`

Comandos:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Base de datos

Se dejo `docker-compose.yml` con PostgreSQL 16 para entorno local. El puerto anfitrion es `5433` para evitar conflictos con instalaciones locales que ya usan `5432`.

```powershell
docker compose up -d postgres
```

## IA

Archivos de configuracion:

- `ai-engine/pyproject.toml`
- `ai-engine/ai_engine/inference/health.py`

Comandos:

```powershell
cd ai-engine
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ai_engine.inference.health
```
