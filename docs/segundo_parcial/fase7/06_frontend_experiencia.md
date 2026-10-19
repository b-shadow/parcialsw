# Experiencia frontend

## Panel flotante

Todos los miembros ven actividad con actor, accion, recurso y fecha. La carga incremental conserva un cursor estable. Solo propietario y organizador ven `Versiones`, `Guardar version` y restauracion.

Guardar usa un dialogo con nombre, descripcion, alcance y revision. Evita doble envio con idempotencia. Restaurar primero solicita una vista previa, muestra conteos y aclara que conversaciones, miembros, bitacora, notificaciones y artefactos no cambian.

Al completar se informa el numero restaurado y el respaldo creado. La pagina recarga contenido mediante el callback existente y mediante `PROJECT_STATE_INVALIDATED`.

## Bandeja

`NotificationCenter` vive en el layout autenticado, separado del control para habilitar Push. Incluye badge `99+`, estados leido/no leido, carga incremental, reintento, marcado masivo y navegacion por rutas internas.

En movil paneles y dialogos respetan el ancho disponible. Los iconos tienen etiquetas, los resultados usan `aria-live` y los controles mantienen dimensiones estables.

