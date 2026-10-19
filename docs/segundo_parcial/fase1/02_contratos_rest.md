# Contratos REST

Todas las rutas usan el prefijo `/api/v1`, requieren JWT y verifican membresia antes de revelar recursos.

## Especificaciones UML

| Metodo | Ruta | Resultado |
| --- | --- | --- |
| GET | `/uml/methods/{method_id}/specification` | Especificacion o `null` para metodos heredados |
| PUT | `/uml/methods/{method_id}/specification` | Alta o reemplazo idempotente |
| PATCH | `/uml/methods/{method_id}/specification` | Actualizacion parcial validada |

`user_action` exige contratos backend y Flutter. `api` exige contrato backend. Las referencias de clases deben pertenecer al mismo diagrama y cada campo Flutter debe apuntar a un parametro existente.

## Asistente por proyecto

| Metodo | Ruta | Regla |
| --- | --- | --- |
| GET | `/projects/{id}/ai/settings` | Miembro; crea defaults de forma perezosa |
| PUT | `/projects/{id}/ai/settings` | Propietario u organizador |
| GET | `/projects/{id}/ai/conversation` | Miembro; conversacion unica |
| GET | `/projects/{id}/ai/messages` | Cursor por secuencia |
| GET | `/projects/{id}/ai/actions` | Lectura filtrada y acotada |
| GET | `/projects/{id}/ai/actions/{action_id}` | Accion perteneciente al proyecto |
| GET | `/projects/{id}/ai/recommendations` | Filtro de estado y severidad |

La fase no publica un endpoint de interaccion falso. `AiInteractionRequest` y su respuesta quedan definidos para el orquestador de la Fase 2.

## Tema Flutter

| Metodo | Ruta | Regla |
| --- | --- | --- |
| GET | `/projects/{id}/flutter-theme` | Miembro; defaults para proyecto anterior |
| PUT | `/projects/{id}/flutter-theme` | Editor u organizador; configuracion estricta |

## Lectura movil

| Metodo | Ruta | Contenido |
| --- | --- | --- |
| GET | `/mobile/projects` | Proyectos accesibles y conteos |
| GET | `/mobile/projects/{id}/diagrams` | Resumen de diagramas |
| GET | `/mobile/diagrams/{id}` | UML completo de solo lectura |

No existen rutas `POST`, `PUT`, `PATCH` o `DELETE` bajo `/mobile` en esta fase.

## Codigos relevantes

- `401`: token ausente o invalido.
- `403`: sin membresia o rol requerido.
- `404`: recurso inexistente dentro del alcance autorizado.
- `409`: snapshot o conversacion incompatible.
- `422`: contrato, cursor, referencia o parametro invalido.

