# Migraciones y compatibilidad

## Revision

- Revision: `d4e8f1a2b3c4`
- Revision anterior: `b21a9d4c6e70`
- Head confirmado: `d4e8f1a2b3c4`

La migracion crea las siete tablas nuevas en orden de dependencias, sus claves foraneas, indices, restricciones unicas y `CHECK`. El `downgrade()` elimina exclusivamente estructuras de esta fase en orden inverso.

## Compatibilidad hacia atras

- No se modifica ni elimina una columna anterior.
- `uml_methods` no requiere backfill; una especificacion ausente es valida.
- Tema, configuracion IA y conversacion se crean al primer acceso.
- Snapshots sin `schema_version` se interpretan como V1.
- Los modelos UML V1 sin `specification` usan `None`.
- Clientes WebSocket v1 siguen siendo aceptados.
- La generacion Flutter sin tema persistido conserva defaults historicos.

## Restauracion

1. Bloquear proyecto y comprobar rol Organizador.
2. Parsear y validar V1/V2 antes de cambiar datos.
3. Rechazar versiones futuras con `409`.
4. Crear snapshot V2 de respaldo.
5. Restaurar diagramas y especificaciones.
6. Restaurar tema, ajustes de generacion e IA no sensible.
7. Registrar auditoria y evento de colaboracion.

## Evidencia

`alembic upgrade head --sql` genero SQL PostgreSQL completo sin errores. Como el servicio instalado estaba detenido y Windows nego iniciarlo, se creo un cluster PostgreSQL 17 efimero y aislado en el directorio temporal, sobre el puerto `55432`.

En ese cluster se ejecuto:

1. Upgrade hasta `b21a9d4c6e70`.
2. Insercion de usuario, proyecto, diagrama, clase y metodo representativos del primer parcial.
3. Upgrade a `d4e8f1a2b3c4`.
4. Insercion de especificacion, configuracion IA, conversacion, mensaje y tema.
5. Downgrade de una revision.
6. Verificacion de que el metodo anterior seguia presente y las tablas nuevas ya no existian.
7. Segundo upgrade al head.
8. Verificacion de revision, datos anteriores y tablas nuevas.

El servidor efimero fue detenido y su directorio temporal fue eliminado al terminar. No se uso SQLite porque no representa JSONB, UUID ni restricciones PostgreSQL.

Comandos para una base de prueba disponible:

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe downgrade -1
.\.venv\Scripts\alembic.exe upgrade head
```

## Endurecimiento posterior de roles

La revision `c9d3e4f5a6b7` normaliza asignaciones globales historicas, conserva un solo rol por usuario con prioridad `ADMINISTRADOR` sobre `EDITOR`, transforma asignaciones globales antiguas de `ORGANIZADOR` a `EDITOR` y elimina `ORGANIZADOR` del catalogo global. Los roles por proyecto permanecen intactos en `project_members`.

