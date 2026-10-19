# Normalizacion y compatibilidad

## Pipeline autoritativo

1. Detectar version.
2. Adaptar v1 a v2.
3. Completar paletas con defaults.
4. Normalizar hexadecimal.
5. Validar catalogos, limites y campos extra.
6. Calcular contraste.
7. devolver tema, diagnosticos y campos normalizados.

La implementacion autoritativa es `normalize_theme()` en backend. React contiene funciones puras equivalentes para respuesta inmediata, pero guardar siempre pasa por `POST /validate` o por la validacion transaccional del `PUT`.

## Compatibilidad v1

Se conservan solicitudes con `primary_color`, `font_family`, `border_radius`, `button_style` y `density`. El adaptador calcula colores de texto seguros, replica el radio inicial y conserva la intencion visual. Fuentes antiguas no catalogadas se mantienen solo en el camino de generacion legado; un tema v2 nuevo las rechaza.

El guardado bloquea la fila de tema durante la comprobacion de revision. Una carrera sobre una fila aun inexistente se convierte en conflicto `409` mediante la restriccion unica. Un PUT identico no incrementa revision, no crea auditoria adicional y no publica un evento WebSocket.

## Retiro

V1 permanece durante el segundo parcial para artefactos y clientes existentes. Su retiro requiere que no existan configuraciones v1 persistidas y que las integraciones externas hayan migrado a `schema_version: 2`.
