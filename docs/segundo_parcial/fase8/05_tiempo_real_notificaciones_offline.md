# Tiempo real, notificaciones y offline

## WebSocket

`ProjectRealtime` autentica con los subprotocolos `case-v1` y `case-auth.<JWT>`, envia heartbeat y reconecta con backoff exponencial de 1 a 32 segundos. Mantiene hasta 500 `event_id` vistos para no procesar duplicados. Los eventos relevantes refrescan el detalle con debounce.

## Notificaciones

La bandeja consulta notificaciones persistentes, filtra no leidas y registra apertura. El contador global y los contadores por proyecto provienen del backend; ya no son valores fijos. Mientras la aplicacion esta abierta, WebSocket actualiza los recursos relacionados.

El backend existente usa Web Push para la PWA web. Flutter no simula Web Push del navegador: una notificacion nativa con la aplicacion cerrada requerira integrar APNs/FCM y sus credenciales en una fase operativa. La bandeja persistente no pierde eventos por esa limitacion.

## Offline honesto

- Perfil, lista de proyectos y diagramas abiertos se cachean por usuario.
- Sin backend se muestra la ultima copia disponible y el topbar indica modo sin conexion.
- No se cachean contrasenas, tokens en texto plano ni respuestas de mutaciones.
- IA, marcado de avisos y cambio de clave requieren backend.
- No existe cola silenciosa de acciones.

Al cerrar sesion se purga toda la cache asociada al usuario.
