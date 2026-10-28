# Guía de desarrollo

## Añadir un contrato

1. Crear o versionar un modelo en `contracts.py`.
2. Añadir su validador BSON en `schema.py`.
3. Definir índices con nombres estables.
4. Registrar el modelo en `DOCUMENT_MODELS` si recibirá Outbox.
5. Añadir repositorio y pruebas unitarias/reales.
6. Documentar compatibilidad y migración.

## Fechas e identificadores

- generar UUID en la aplicación;
- serializar UUID como texto canónico;
- usar `datetime.now(UTC)`;
- no guardar fechas como texto en BSON;
- calcular hashes con JSON canónico.

## Escritura entre almacenes

No se debe llamar MongoDB dentro de una transacción SQL de negocio. Se encola una `MongoMutation` con una clave idempotente determinista y el worker realiza la operación.

## Errores

- `MongoUnavailableError`: cliente no inicializado;
- `MongoSchemaError`: bootstrap inválido;
- `MongoContractError`: reservado para traducción de contratos de aplicación;
- errores PyMongo: reintento del Outbox o readiness degradado.

No capturar excepciones para continuar silenciosamente con datos parciales.

## Evolución por fases

- Fase 11 conecta mensajes y contexto.
- Fase 12 conecta versiones UML.
- Fase 13 conecta el diagrama editable.
- Fase 14 retira duplicación y endurece respaldo.

Cada conexión futura debe conservar autorización SQL, emitir Outbox en la transacción original y activar lectura Mongo sólo después de una reconciliación completa.
