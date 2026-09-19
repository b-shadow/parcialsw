# Fase 3 - Scripts iniciales de base de datos

## Script de esquema

Archivo:

- `docs/fase3/sql/001_modelo_persistencia_inicial.sql`

Contenido:

- Creacion de tabla `alembic_version`.
- Creacion de 24 tablas de dominio.
- Creacion de claves primarias.
- Creacion de claves foraneas.
- Creacion de restricciones unicas.
- Creacion de indices.

## Script de datos iniciales

Archivo:

- `docs/fase3/sql/002_datos_iniciales.sql`

Datos:

- Rol `ADMINISTRADOR`.
- Rol `EDITOR`.
- Rol `ORGANIZADOR`.

## Migraciones ejecutables

Archivos:

- `backend/migrations/versions/3984b20ad386_initial_persistence_model.py`
- `backend/migrations/versions/c081b7d17f22_seed_system_roles.py`

## Validacion aplicada

Se ejecuto:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Resultado:

- Esquema creado correctamente en PostgreSQL.
- Roles base insertados correctamente.
- Metadata SQLAlchemy reconoce 24 tablas de dominio.
- PostgreSQL contiene 25 tablas incluyendo `alembic_version`.

