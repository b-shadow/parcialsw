# Acciones y recomendaciones compartidas

## Acciones

Una respuesta puede proponer varias acciones ordenadas y con dependencias. Se persisten con riesgo, objetivo, payload, confirmacion requerida, clave idempotente y estado.

```text
proposed -> confirmed -> executing -> applied
proposed -> rejected
confirmed/executing -> failed
```

Confirmar implica ejecutar mediante servicios de dominio existentes. El backend valida rol, propiedad del diagrama, version base, dependencias y payload. Dos confirmaciones simultaneas no duplican el cambio: la segunda obtiene el resultado aplicado como respuesta idempotente.

`AI_ACTION_PROPOSED` y `AI_ACTION_STATUS_CHANGED` actualizan todos los clientes. La UI permite aplicar o rechazar solo cuando el estado es `proposed`; ante 403/409 refresca el estado compartido.

## Recomendaciones

Las recomendaciones son observaciones no ejecutables con severidad `info`, `warning` o `critical`. Sus transiciones disponibles son `accepted`, `dismissed` y `resolved`, con usuario, fecha y nota de resolucion. Una recomendacion resuelta no puede reabrirse mediante el endpoint actual.

## Referencias

Las referencias tipadas admiten proyecto, diagrama, clase, atributo, metodo, relacion, version, generacion y mensaje. Cada referencia lleva ID y etiqueta; no se interpreta HTML recibido del motor.

## Notificaciones

El sistema evita ruido: solo genera push para una accion propuesta de riesgo alto, una recomendacion critica o una accion aplicada. Los eventos ordinarios se muestran en tiempo real dentro del proyecto. El emisor se excluye de la notificacion push.
