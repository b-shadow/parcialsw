# Pruebas de la fase 4

## Backend especifico

Archivo: `backend/tests/test_second_part_phase4_method_specifications.py`.

Casos cubiertos:

1. normalizacion y rechazo de campos desconocidos;
2. seguridad de rutas backend;
3. borradores incompletos permitidos;
4. validacion estricta bloqueante;
5. contrato listo con `LocalDate` y `date_picker`;
6. exposicion privada invalida;
7. GET mutante y parametro de ruta desconocido;
8. confirmacion obligatoria para eliminar;
9. conflicto de revision con detalle estable;
10. round-trip XMI de parametros y especificacion;
11. adaptador inmutable v1 a v2;
12. rechazo de versiones futuras;
13. contratos OpenAPI para firma, especificacion y refinamiento.

## Frontend especifico

Archivo: `frontend/src/modules/modelado_uml_inteligente/services/umlService.phase4.test.ts`.

Comprueba creacion con `If-None-Match`, actualizacion y borrado con `If-Match`, validacion estricta y refinamiento con identificador idempotente.

## Regresion

Se ejecutan las suites completas de backend y frontend. La prueba de importacion del editor verifica que `readiness`, al ser un dato calculado, no llegue al constructor ORM. Las pruebas WebSocket existentes validan que los eventos v2 convivan con los clientes anteriores.

## Comandos reproducibles

```powershell
cd backend
$env:PYTHONPATH = (Resolve-Path '..\ai-engine').Path
uv run ruff check app migrations
uv run pytest -q

cd ..\ai-engine
uv run ruff check ai_engine tests
uv run pytest -q

cd ..\frontend
npm run lint
npm test -- --run
npm run build
```

## Criterio de aprobacion

La fase cierra solamente si linters, pruebas y compilacion terminan sin errores. Las advertencias de tamano de bundle no alteran el comportamiento y quedan como optimizacion posterior, no como defecto funcional de esta fase.

