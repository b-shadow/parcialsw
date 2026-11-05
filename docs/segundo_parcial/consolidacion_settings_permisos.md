# Consolidación de configuración y permisos del proyecto

## Decisión aplicada

- `projects.settings.ai` contiene la configuración única del asistente por proyecto. La API `GET/PUT /projects/{id}/ai/settings` conserva el contrato anterior; la lectura ya no inserta filas. La escritura bloquea la fila de `projects`, valida la configuración y aumenta `projects.revision` si cambia.
- `project_members.project_role` determina todos los permisos locales mediante el catálogo fijo `ROLE_DEFAULTS`: `ORGANIZADOR`, `EDITOR` y `LECTOR`. Se retiró la ruta de concesiones individuales y la tabla `project_permissions`. Los permisos que llegan al contexto del asistente usan el mismo catálogo.
- `projects.settings.flutter_theme` guarda el tema Flutter activo y su revisión independiente. La actualización bloquea la fila del proyecto y sigue rechazando revisiones obsoletas. `flutter_theme_presets` conserva los temas reutilizables; `notification_preferences` depende de usuario, proyecto y categoría.
- La migración Alembic `a4f6c8d0e2b3` copia íntegramente `ai_project_settings` a `projects.settings.ai` antes de eliminar esa tabla. La migración `b6d8e0f2a4c5` copia `flutter_theme_settings` a `projects.settings.flutter_theme`. Ambas conservan identificadores, revisión y marcas de auditoría. Las concesiones individuales se descartan porque ya no tienen efecto. El downgrade reconstruye las configuraciones y crea vacía la antigua tabla de permisos.

## Roles fijos

| Rol | Permisos |
| --- | --- |
| ORGANIZADOR | Todos los códigos de `PERMISSION_CODES` |
| EDITOR | `project.read`, `uml.edit`, `versions.create`, `ai.chat`, `ai.confirm_actions`, `generation.run`, `theme.edit` |
| LECTOR | `project.read`, `ai.chat` |

Un rol desconocido no recibe permisos. Para cambiar el alcance de una persona se cambia su rol de proyecto, no sus permisos particulares. Los permisos globales de administración de usuarios son independientes de estos roles locales.

## Compatibilidad

El diccionario de tablas SQL es [bd.md](bd.md). Los endpoints del asistente y del tema conservan sus contratos. Los snapshots de versiones restauran ambas configuraciones en `projects.settings`. La migración `a4f6c8d0e2b3` se aplicó y verificó con los datos locales. La base del proyecto, configurada en el puerto 5433, está detenida actualmente; `b6d8e0f2a4c5` se aplicará con `alembic upgrade head` cuando esa base esté disponible. Entonces debe regenerarse `bd.md` con `python -m scripts.generate_db_dictionary` para reflejar las 29 tablas finales.
