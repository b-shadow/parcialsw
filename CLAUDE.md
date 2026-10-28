# CASE Inteligente (parcialsw) — Guía de Desarrollo

Monorepo para la plataforma CASE Inteligente (Ingeniería de Software I · UAGRM 2-2026).

## Estructura del Proyecto
- `backend/`: API FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 16 (+ Redis opcional).
- `frontend/`: Single-Page Application en React 19 + Vite 6 + TypeScript + Tailwind CSS + zustand.
- `ai-engine/`: Motor de IA local offline (Ollama / Qwen + motor de reglas de respaldo).
- `mobile/`: Aplicación Flutter multiplataforma (Android/iOS) en modo lectura y notificaciones.
- `docs/segundo_parcial/mejoras-2p/`: Plan maestro (`PLAN.md`), maqueta interactiva y tareas `V0.1` a `V3.4`.

## Plan Maestro y Contratos
- Consulta siempre `docs/segundo_parcial/mejoras-2p/PLAN.md` (secciones 4 Contratos y 6 Archivo por archivo).
- Bitácora de trabajo colaborativo: `docs/segundo_parcial/mejoras-2p/bitacora-agentes.md`.

## Comandos de Verificación (PowerShell)
```powershell
# Backend (pruebas unitarias y de integración)
cd backend; .\.venv\Scripts\python.exe -m pytest -q; cd ..

# Frontend (pruebas, linter y build de producción)
cd frontend; npm run test; npm run lint; npm run build; cd ..

# Motor de IA
cd ai-engine; pytest -q; cd ..
```

## Reglas Clave de Implementación
1. **Contratos inmutables:** No alterar nombres de endpoints, eventos WebSocket ni tipos compartidos sin actualizar `PLAN.md`.
2. **Migración única:** Solo `V0.1` genera migraciones Alembic (`f1a2b3c4d5e6`). No crear cabezas paralelas.
3. **NoSQL opcional:** Redis es opcional en desarrollo (`REDIS_ENABLED=false`). Con Redis inactivo la app degrada sin error 500.
4. **Seguridad:** Ninguna clave, secreto o token en código ni commits (`.env` está ignorado en Git).
5. **Componentes compartidos:** Usar los componentes de `V0.5` (`Toaster`, `ConfirmDialog`, `Avatar`, `StatusBadge`, `EmptyState`, `Skeleton`). Nunca `window.confirm` ni `alert`.
