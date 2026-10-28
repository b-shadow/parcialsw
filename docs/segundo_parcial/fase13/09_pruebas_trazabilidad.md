# Pruebas y trazabilidad

| Criterio | Evidencia automatizada |
|---|---|
| Contenido UML completo | Serializacion de clases, atributos, metodos, parametros, especificaciones, relaciones y visuales |
| Edicion sin perdida | Integracion real SQL -> Outbox -> Mongo y lectura del resultado |
| Conflictos controlados | `expected_revision`, incremento exacto y segundo intento rechazado |
| Actualizacion parcial | Test de `$set` con `array_filters` por ID |
| Referencias validas | Rechazo de relacion con destino inexistente |
| XMI soportado | Suite de roundtrip para herencia, agregacion, composicion y clase asociativa |
| Generacion correcta | `GenerationService` consume modelo canonico y suite de generadores existente |
| Hashes y reanudacion | Migrador ejecutado y repetido sin duplicacion |
| Rollback | Pruebas Mongo-first, documento atrasado y fallback SQL |
| Despliegue | Readiness condicionado, Alembic unico y Compose valido |

Archivos principales: `test_phase13_active_uml_diagrams.py` y `test_phase13_uml_diagrams_integration.py`. La prueba real se ejecuta en CI con PostgreSQL 16 y MongoDB 8; localmente se omite cuando no existen `DATABASE_URL` y `MONGODB_TEST_URI` de integracion.
