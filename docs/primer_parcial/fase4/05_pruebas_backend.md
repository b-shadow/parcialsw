# Fase 4 - Pruebas backend

## Pruebas implementadas

Archivo:

- `backend/tests/test_phase4_contracts.py`

## Flujo cubierto

Las pruebas automatizadas validan:

1. Hash y verificacion de contrasenas.
2. Creacion y decodificacion de JWT.
3. Health checks de backend y modulos.
4. Publicacion de rutas OpenAPI funcionales.
5. Contrato WebSocket colaborativo por proyecto.

## Comandos ejecutados

```powershell
cd backend
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

## Resultado

- `ruff check .`: correcto.
- `pytest -q`: 3 pruebas correctas.

Advertencias observadas:

- Deprecation warnings de `fastapi.testclient`/Starlette por compatibilidad futura. No bloquean la ejecucion ni el comportamiento validado.
