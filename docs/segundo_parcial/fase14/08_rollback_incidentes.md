# Rollback e incidentes

## MongoDB no disponible

1. Detener escrituras o poner la API fuera de readiness.
2. No activar fallback SQL: las tablas de contenido fueron retiradas. Para volver al estado anterior se restaura el backup coordinado previo al corte.
3. Recuperar MongoDB o restaurar el ultimo backup coordinado.
4. Drenar Outbox y ejecutar reconciliacion.
5. Reabrir trafico solo con gate completado.

## Divergencia o revision atrasada

No se fuerza el hash ni se reduce revision. Se inspecciona el evento Outbox, se corrige la causa y se reprocesa idempotentemente. Un conflicto de igual revision y distinto hash requiere intervencion humana.

## Restauracion fallida

La restauracion normal rechaza destinos no vacios y valida todo el archivo antes de escribir. En un entorno limpio, ante fallo se descarta el entorno y se repite desde el mismo ZIP. `--force` requiere snapshot previo y ventana de mantenimiento.
