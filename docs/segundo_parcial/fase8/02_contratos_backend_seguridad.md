# Contratos backend y seguridad

## Endpoints moviles

| Metodo | Ruta | Uso |
|---|---|---|
| GET | `/api/v1/mobile/projects` | Resumen autorizado de proyectos |
| GET | `/api/v1/mobile/projects/{id}/diagrams` | Diagramas del proyecto |
| GET | `/api/v1/mobile/diagrams/{id}` | Modelo UML completo de lectura |
| GET | `/api/v1/mobile/projects/{id}/generations` | Estado de generaciones coordinadas |

La familia `/mobile` solo publica `GET`. Una prueba sobre OpenAPI falla si aparece `POST`, `PUT`, `PATCH` o `DELETE` bajo ese prefijo.

## Reutilizacion

Actividad, versiones, IA y notificaciones usan las rutas existentes de Fases 2 a 7. No se duplican permisos. Cada servicio verifica membresia en backend.

## Solo lectura

`MobileReadService.get_diagram()` devuelve `can_edit=false` sin importar que el usuario sea organizador o editor. Flutter vuelve a verificarlo y rechaza una respuesta que contradiga el contrato. La UI no contiene guardar, borrar, mover ni restaurar.

## Sesion y cache

- El JWT se almacena en Keychain/Keystore mediante `flutter_secure_storage`.
- La cache no guarda credenciales ni cuerpos de contrasena.
- Todas las claves de cache incluyen el UUID del usuario.
- Cerrar sesion elimina token y cache del usuario.
- Un HTTP 401 invalida la sesion; no se usa cache para simular una sesion expirada.

## IA movil

Las solicitudes envian `requested_context.surface=mobile_readonly`. El backend conserva el mismo orquestador y memoria. Flutter muestra respuestas y propuestas, pero no confirma acciones estructurales.
