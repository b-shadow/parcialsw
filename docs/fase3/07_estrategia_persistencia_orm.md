# Fase 3 - Estrategia de persistencia ORM

## Stack

- PostgreSQL como base de datos principal.
- SQLAlchemy 2.x como ORM.
- Alembic como gestor de migraciones.
- Pydantic para validacion de entrada/salida en fases de API.

## Organizacion ORM

Los modelos se ubican dentro de cada paquete funcional:

```text
backend/app/modules/
|-- acceso_usuarios/models/
|-- proyectos_colaboracion/models/
|-- modelado_uml/models/
`-- generacion_software/models/
```

El archivo `backend/app/models.py` importa todos los modelos para registrar metadata completa en Alembic.

## Base comun

`backend/app/core/database/session.py` define:

- `Base`
- `engine`
- `SessionLocal`
- `get_db`

`backend/app/core/database/mixins.py` define:

- `UuidPrimaryKeyMixin`
- `TimestampMixin`

## Migraciones

Archivos principales:

- `backend/alembic.ini`
- `backend/migrations/env.py`
- `backend/migrations/script.py.mako`
- `backend/migrations/versions/3984b20ad386_initial_persistence_model.py`
- `backend/migrations/versions/c081b7d17f22_seed_system_roles.py`

Comandos:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "mensaje"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

## Versionamiento de esquema

La tabla `alembic_version` controla la version aplicada. El estado actual aplicado es:

- `c081b7d17f22`

## Criterio de evolucion

- Nuevas tablas deben ubicarse en el modulo funcional propietario.
- Relaciones transversales deben usar claves foraneas explicitas.
- Cambios de esquema deben realizarse mediante Alembic.
- Datos base del sistema deben insertarse por migraciones idempotentes.

