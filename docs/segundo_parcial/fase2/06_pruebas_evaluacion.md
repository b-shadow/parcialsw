# Pruebas y evaluacion

## Comandos ejecutados

```powershell
backend\.venv\Scripts\python.exe -m ruff check ai-engine/ai_engine ai-engine/tests backend/app backend/tests
backend\.venv\Scripts\python.exe -m pytest -q ai-engine/tests
cd backend
.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm test -- --run
npm run build
npm run lint
```

## Resultado de cierre

| Componente | Resultado |
| --- | --- |
| Ruff Python | Aprobado |
| AI engine | 43 aprobadas y 1 omitida por ausencia de Ollama real |
| Backend | 50 aprobadas |
| Frontend Vitest | 14 aprobadas |
| TypeScript + Vite | Aprobado |
| ESLint | Aprobado |

El build conserva una advertencia no bloqueante por un chunk mayor a 500 kB. No es una regresion de esta fase.

## Cobertura funcional

- URL local valida y destinos inseguros rechazados.
- Salud y modelo instalado/ausente.
- JSON Schema enviado a `/api/chat`.
- Reparacion de salida invalida.
- Metricas transformadas.
- Multiintencion, orden y negacion.
- Edicion sobre diagrama activo.
- Dependencias y ciclos.
- Riesgo y confirmacion.
- Aclaracion de referencias ambiguas.
- Negativa ante secretos e inyeccion.
- Presupuesto sin JSON truncado.
- Redaccion de secretos del contexto.
- OpenAPI con interaccion, salud, confirmacion y rechazo.
- Contratos TypeScript y URLs del cliente.
- Endpoints legacy sin regresion.

## Ollama real

`Get-Command ollama` devolvio `OLLAMA_NOT_INSTALLED`. La prueba `test_real_ollama_runtime_when_installed` se omite en ese entorno. No se instalo ni descargo Qwen automaticamente, de acuerdo con la politica de la fase.

## Base de datos

La persistencia usa las tablas verificadas en fase 1. La comprobacion de conexion PostgreSQL local no respondio dentro del tiempo de validacion actual, por lo que no se declara una integracion real nueva contra base activa. Los contratos ORM, OpenAPI y toda la suite backend si fueron validados; la migracion de fase 1 conserva el modelo requerido y alinea el modelo Qwen por defecto.
