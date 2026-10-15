# Backend principal

Backend FastAPI de la plataforma CASE inteligente. La estructura inicial respeta los cuatro paquetes funcionales definidos en la documentacion:

- `acceso_usuarios`
- `proyectos_colaboracion`
- `modelado_uml`
- `generacion_software`

## Ejecucion local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip install -e ..\ai-engine
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Endpoints iniciales

- `GET /health`
- `GET /api/v1/acceso-usuarios/health`
- `GET /api/v1/proyectos-colaboracion/health`
- `GET /api/v1/modelado-uml/health`
- `GET /api/v1/generacion-software/health`
- `WS /ws/projects/{project_id}`

## Endpoints funcionales de Fase 4

Autenticacion y usuarios:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/users`
- `PATCH /api/v1/users/{user_id}`

Proyectos y colaboracion:

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `PATCH /api/v1/projects/{project_id}`
- `DELETE /api/v1/projects/{project_id}`
- `POST /api/v1/projects/{project_id}/members`
- `GET /api/v1/projects/{project_id}/members`
- `POST /api/v1/projects/{project_id}/members/{member_id}/permissions`
- `POST /api/v1/projects/{project_id}/versions`
- `GET /api/v1/projects/{project_id}/versions`
- `POST /api/v1/projects/{project_id}/versions/{version_id}/restore`
- `GET /api/v1/projects/{project_id}/changes`

### Colaboracion WebSocket

El canal `WS /ws/projects/{project_id}` aplica las siguientes garantias:

- autentica el JWT durante el handshake mediante el subprotocolo `case-auth.*`;
- valida origen, usuario activo y membresia del proyecto;
- revalida sesion y membresia con el latido `PING/PONG`;
- confirma cada cambio con `EVENT_ACK` y `client_event_id`;
- evita duplicados despues de una reconexion;
- asigna `sequence_number` por proyecto para detectar mensajes perdidos;
- limita conexiones y aplica timeout de envio a clientes lentos;
- desconecta inmediatamente a un usuario retirado del proyecto.

El despliegue actual ejecuta un solo worker de Uvicorn. Si se aumenta a varios workers o varias
instancias, debe agregarse un bus compartido (por ejemplo Redis Pub/Sub) antes de escalar, porque
las conexiones activas viven en memoria del proceso.

Modelado UML:

- `POST /api/v1/uml/diagrams`
- `GET /api/v1/uml/projects/{project_id}/diagrams`
- `POST /api/v1/uml/diagrams/{diagram_id}/classes`
- `GET /api/v1/uml/diagrams/{diagram_id}/classes`
- `POST /api/v1/uml/classes/{class_id}/attributes`
- `POST /api/v1/uml/classes/{class_id}/methods`
- `POST /api/v1/uml/diagrams/{diagram_id}/relationships`
- `POST /api/v1/uml/diagrams/{diagram_id}/validate`

Transformacion y generacion:

- `POST /api/v1/generation/transformations`
- `POST /api/v1/generation/spring-boot`
- `GET /api/v1/generation/spring-boot/{backend_id}/download`
- `POST /api/v1/generation/flutter`

IA local offline:

- `GET /api/v1/ai/profile`
- `POST /api/v1/ai/uml/text`
- `POST /api/v1/ai/uml/voice`
- `POST /api/v1/ai/uml/image`
- `POST /api/v1/ai/uml/validate`
- `POST /api/v1/ai/software/plan`

## Base de datos y migraciones

PostgreSQL local esta configurado en `localhost:5433` mediante `docker-compose.yml`.

```powershell
docker compose up -d postgres
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

La metadata ORM se agrega desde `app/models.py`, importando los modelos de los cuatro paquetes funcionales.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest -q
```
