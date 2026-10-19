# Pruebas multiusuario y verificacion

## Cobertura automatizada agregada

Backend (`test_second_part_phase3_collaboration.py`):

- registro de endpoints de historial y recomendaciones;
- metadatos de paginacion bidireccional;
- referencias ampliadas;
- resumen estructurado, acotado y con acciones pendientes;
- presencia agregada entre pestanas;
- desconexion limpia;
- limite de conexiones por usuario.

Frontend (`projectAiStore.test.ts`):

- mezcla REST/WebSocket sin duplicados;
- orden por secuencia;
- actualizacion del mismo mensaje;
- cursores monotonos ante eventos fuera de orden;
- aislamiento al cambiar de proyecto.

Las pruebas previas cubren autenticacion WebSocket, aislamiento por proyecto, exclusion del emisor, limite por proyecto, idempotencia de eventos y restricciones de version.

## Resultados del cierre

```text
Backend:  56 passed
IA:       43 passed, 1 skipped
Frontend: 17 passed
Ruff backend: passed
ESLint frontend: passed
TypeScript + Vite production build: passed
```

La prueba omitida del motor corresponde a Ollama real, no instalado en este equipo; los contratos del proveedor se verifican con transporte simulado y el fallback offline.

## Escenarios de aceptacion

1. Dos miembros conectados reciben el mismo mensaje y autor.
2. Una accion propuesta no modifica UML antes de confirmar.
3. Un usuario sin permiso no ejecuta cambios.
4. Una reconexion compara cursores y recupera la brecha.
5. Una conversacion extensa genera resumen sin borrar historial.
6. La revocacion se detecta en heartbeat.
7. Confirmaciones simultaneas se resuelven idempotentemente.
