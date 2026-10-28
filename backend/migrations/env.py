from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config.settings import settings
from app.models import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

RETIRED_DOCUMENT_TABLES = {
    "ai_messages",
    "uml_attributes",
    "uml_classes",
    "uml_method_specifications",
    "uml_methods",
    "uml_parameters",
    "uml_relationships",
    "uml_visual_elements",
}


def include_object(object_, name, type_, reflected, compare_to):
    table_name = (
        name if type_ == "table" else getattr(getattr(object_, "table", None), "name", None)
    )
    return table_name not in RETIRED_DOCUMENT_TABLES


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
