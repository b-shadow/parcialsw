# Fase 4 - API REST implementada

## Health

- `GET /health`
- `GET /api/v1/acceso-usuarios/health`
- `GET /api/v1/proyectos-colaboracion/health`
- `GET /api/v1/modelado-uml/health`
- `GET /api/v1/generacion-software/health`

## Acceso, usuarios y seguimiento

- `POST /api/v1/auth/register`: registra usuario con rol base Editor.
- `POST /api/v1/auth/login`: valida credenciales y emite JWT.
- `GET /api/v1/auth/me`: devuelve usuario autenticado.
- `GET /api/v1/users`: lista usuarios autenticados.
- `PATCH /api/v1/users/{user_id}`: actualiza datos permitidos.

## Proyectos y colaboracion

- `POST /api/v1/projects`: crea proyecto y asigna Organizador interno al creador.
- `GET /api/v1/projects`: lista proyectos del usuario.
- `GET /api/v1/projects/{project_id}`: consulta proyecto accesible.
- `PATCH /api/v1/projects/{project_id}`: actualiza proyecto como Organizador.
- `DELETE /api/v1/projects/{project_id}`: archiva proyecto.
- `POST /api/v1/projects/{project_id}/members`: agrega integrante.
- `GET /api/v1/projects/{project_id}/members`: lista integrantes.
- `POST /api/v1/projects/{project_id}/members/{member_id}/permissions`: asigna permiso interno.
- `POST /api/v1/projects/{project_id}/versions`: crea version/snapshot.

## Modelado UML inteligente

- `POST /api/v1/uml/diagrams`: crea diagrama de clases.
- `GET /api/v1/uml/projects/{project_id}/diagrams`: lista diagramas de proyecto.
- `POST /api/v1/uml/diagrams/{diagram_id}/classes`: crea clase UML y posicion visual.
- `GET /api/v1/uml/diagrams/{diagram_id}/classes`: lista clases.
- `POST /api/v1/uml/classes/{class_id}/attributes`: agrega atributo.
- `POST /api/v1/uml/classes/{class_id}/methods`: agrega metodo.
- `POST /api/v1/uml/diagrams/{diagram_id}/relationships`: crea relacion UML.
- `POST /api/v1/uml/diagrams/{diagram_id}/validate`: valida estructura UML.

## Transformacion y generacion

- `POST /api/v1/generation/transformations`: transforma UML en modelo intermedio.
- `POST /api/v1/generation/spring-boot`: registra generacion backend Spring Boot.
- `POST /api/v1/generation/flutter`: registra generacion frontend Flutter.

