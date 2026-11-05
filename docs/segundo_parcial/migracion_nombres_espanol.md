# Nombres de persistencia en español

## Identificadores del código

Se renombraron módulos, clases y funciones del backend, del motor de IA, del frontend y de Flutter. Los paquetes del asistente, modelado UML, proyectos, notificaciones y generación usan nombres propios en español; el gestor de conexiones WebSocket está en `app/websocket/gestor_conexiones.py`. Las exportaciones `__all__` del backend y del motor de IA se alinearon con los nuevos nombres. En el frontend, `principal.tsx` y `Aplicacion.tsx` son el punto de entrada y componente propios; `main.dart` permanece como punto de entrada exigido por Flutter.

Este renombrado de código es distinto del renombrado físico de las bases. Persisten atributos internos en inglés en modelos ORM, Pydantic, TypeScript y Dart; el adaptador los convierte en las fronteras PostgreSQL, MongoDB y HTTP. Por ello, **no corresponde afirmar que todo el código propio esté todavía en español**. Los nombres de API obligatorios de SQLAlchemy, Pydantic, MongoDB, React, FastAPI y Flutter deben conservarse. Las migraciones históricas también retienen identificadores antiguos para poder actualizar instalaciones existentes.

Después de los cambios de código se ejecutaron las pruebas con PostgreSQL y MongoDB aislados: backend, 222 aprobadas y 2 omitidas; motor de IA, 67 aprobadas y 1 omitida; frontend, 77 aprobadas y compilación de producción; Flutter, análisis sin incidencias y 4 pruebas aprobadas. Ruff pasa en backend y motor de IA.

## Alcance

El esquema **activo de PostgreSQL** utiliza nombres en español para sus 28 tablas de aplicación, columnas, restricciones e índices. `alembic_version` conserva su nombre obligatorio de Alembic. Los modelos ORM y el repositorio del asistente usan nombres de clase y métodos en español. Por ejemplo, `ai_processes.model_name` pasó a `procesos_ia.nombre_modelo`, y `AssistantRepository.get_message` pasó a `RepositorioAsistente.obtener_mensaje`.

La configuración JSONB de `proyectos.configuracion` guarda `ia.nombre_modelo`, `tema_flutter` y `configuracion_generacion`. El adaptador del ORM mantiene nombres internos para los servicios. Los valores de enumeraciones y las claves de opciones libres conservan su significado original.

MongoDB usa siete colecciones con nombres en español: `diagramas_uml`, `versiones_diagrama_uml`, `mensajes_ia`, `instantaneas_contexto_ia`, `puntos_control_migracion`, `eventos_nosql_procesados` y `auditorias_operativas_nosql`. Sus campos estructurales, el contenido UML, los validadores y los índices se traducen en la frontera de persistencia. Los modelos de dominio siguen operando sobre las mismas estructuras en memoria para no alterar el cálculo de hashes ni la generación de código.

El frontend intercambia JSON en español con HTTP mediante `X-Contrato-Idioma: es` y con WebSocket mediante `?contrato=es`. Un adaptador en cada extremo convierte el JSON al modelo interno. Los clientes sin ese encabezado conservan temporalmente el contrato anterior. El catálogo de campos compartido se encuentra en `backend/app/core/api/nombres_contratos.py` y `frontend/src/core/api/nombresContrato.json`; una prueba detecta cualquier diferencia. Los nombres de rutas y los valores de enumeraciones se mantienen, ya que son identificadores de protocolo y no campos JSON.

## Secuencia de migraciones

1. `a4f6c8d0e2b3`: roles fijos y configuración de IA en el proyecto.
2. `b6d8e0f2a4c5`: tema Flutter en la configuración del proyecto.
3. `c7e9f1a3b5d6`: renombra tablas y columnas físicas sin recrearlas.
4. `d8f0a2b4c6e7`: convierte las claves conocidas del JSONB.
5. `e9a1b3c5d7f8`: renombra restricciones e índices.

Antes de actualizar una base con datos reales: hacer copia de PostgreSQL, detener escrituras de la aplicación y ejecutar `alembic upgrade head` desde `backend/` con `DATABASE_URL` apuntando a esa base. Los identificadores y claves foráneas se conservan. No editar migraciones anteriores: sus nombres históricos son necesarios para actualizar instalaciones antiguas. El rollback se verificó con `alembic downgrade -1` y nuevo `upgrade head` en una base aislada.

Hacer también una copia de MongoDB antes de arrancar el backend nuevo. Durante el arranque, `ensure_mongo_schema` renombra colecciones antiguas, convierte los documentos existentes de forma reanudable, activa validadores e índices españoles y retira índices con nombres antiguos. Detener todas las instancias anteriores y arrancar una sola instancia nueva durante esta conversión. Si aparecen simultáneamente una colección antigua y su destino, el arranque se detiene para evitar sobrescrituras; resolverlo con el respaldo antes de continuar. Para volver al esquema MongoDB anterior hay que restaurar el respaldo coordinado: no existe downgrade automático de documentos.

## Verificación realizada

- PostgreSQL habitual del proyecto en el puerto `5433`: migración completa desde `a4f6c8d0e2b3` hasta `e9a1b3c5d7f8`; 29 tablas físicas, 28 de aplicación.
- `alembic check`: sin operaciones pendientes entre el ORM y el esquema físico.
- Pruebas del backend con PostgreSQL y MongoDB reales en bases aisladas, incluida conversión de documentos de las siete colecciones y contratos HTTP y WebSocket en español: 222 aprobadas y 2 omitidas por requerir toolchains generados.
- La prueba de migración de Alembic utiliza `CASE_TEST_DATABASE_URL` en una base independiente de `DATABASE_URL`; así sus operaciones de downgrade no alteran los escenarios del asistente. Las acciones propuestas por el asistente se devuelven según el orden del plan para respetar sus dependencias al confirmarlas.
- Los antiguos ensayos de migración de mensajes y clases desde tablas SQL retiradas se sustituyeron por pruebas de los flujos actuales: chat y diagrama con identidad SQL y contenido MongoDB.
- Ruff sin errores; motor de IA: 67 pruebas aprobadas y 1 omitida; frontend: 77 pruebas aprobadas y compilación de producción correcta.
- Reversión de `e9a1b3c5d7f8` a `b6d8e0f2a4c5` y nueva actualización a `head` con preservación de IDs de 10 usuarios, 10 proyectos, 10 diagramas y 11 chats en la base aislada.
- [Diccionario físico](bd.md) regenerado desde la base habitual ya migrada.

## Aplicación sobre los datos del proyecto

Se guardaron respaldos locales fuera de Git en `storage/backups/nombres_es_20261104_postgres.dump`, `storage/backups/nombres_es_20261104_postgres_pg16.dump` y `storage/backups/nombres_es_20261104_mongo.archive.gz`. El respaldo PostgreSQL creado con el cliente 16 se restauró sin errores en una base temporal.

Se compararon las claves primarias de las 28 tablas SQL antes y después: **190 filas conservadas**, con las configuraciones JSONB equivalentes. Se compararon todos los documentos MongoDB contra el respaldo restaurado: **26 documentos idénticos tras la traducción**, incluidos 2 diagramas, 15 mensajes, 7 contextos y 2 auditorías. El ORM y los repositorios MongoDB leyeron correctamente los 2 proyectos, 2 diagramas y 2 chats existentes.
