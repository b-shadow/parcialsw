# Infraestructura y configuración

## Entorno local

`docker-compose.yml` incorpora `mongo:8.0`, volumen `mongodb_data`, autenticación, puerto de host `27018` y health check con `mongosh`.

```bash
docker compose up -d postgres mongodb
docker compose ps
```

La URI local predeterminada es:

```text
mongodb://case_user:case_password@localhost:27018/?authSource=admin
```

## Variables

| Variable | Propósito | Predeterminado de desarrollo |
|---|---|---|
| `MONGODB_URI` | Conexión autenticada | Mongo local en `27018` |
| `MONGODB_DATABASE` | Base documental | `case_inteligente_nosql` |
| `MONGODB_ENABLED` | Habilita integración | `true` |
| `MONGODB_REQUIRED` | Condiciona readiness | `false` |
| `MONGODB_CONNECT_TIMEOUT_MS` | Límite de conexión | `3000` |
| `MONGODB_SERVER_SELECTION_TIMEOUT_MS` | Límite de selección | `3000` |
| `MONGODB_OUTBOX_BATCH_SIZE` | Eventos por lote | `50` |
| `MONGODB_OUTBOX_MAX_ATTEMPTS` | Reintentos antes de `dead` | `8` |

Los límites son validados por Pydantic. Los secretos de producción no se versionan.

## Ciclo de vida

El `lifespan` de FastAPI:

1. crea el cliente asíncrono;
2. ejecuta `ping`;
3. crea o actualiza validadores e índices;
4. mantiene el cliente para el proceso;
5. cierra el cliente de forma asíncrona al terminar.

Un fallo Mongo se registra y refleja en readiness. No transforma el arranque en una excepción cuando Mongo es opcional.

## Producción

`docker-compose.prod.yml` agrega:

- MongoDB sin exponer puerto al host;
- dependencia saludable del backend;
- `MONGODB_REQUIRED=true`;
- worker `nosql-outbox-worker` en ejecución continua;
- volumen persistente independiente.

Variables obligatorias adicionales:

```text
MONGO_ROOT_PASSWORD
```

Se recomienda reemplazar el usuario root por un usuario de aplicación con privilegios limitados antes de un despliegue externo.
