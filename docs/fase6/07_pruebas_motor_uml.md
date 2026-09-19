# Fase 6 - Pruebas del motor UML

## Pruebas agregadas

Archivo:

- `backend/tests/test_phase6_uml_engine.py`

Cobertura:

- Generacion de modelo interno UML desde texto.
- Validacion estructural y recomendaciones.
- Exportacion e importacion XMI.
- Registro de contratos OpenAPI de Fase 6.

## Validacion backend

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado:

- Ruff correcto.
- 7 pruebas correctas.

## Validacion frontend

```powershell
npm run lint
npm run test
npm run build
```

Resultado:

- Lint correcto.
- 1 prueba correcta.
- Build correcto.
