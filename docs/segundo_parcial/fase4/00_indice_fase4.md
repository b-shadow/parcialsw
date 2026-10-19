# Fase 4 - Especificacion funcional de metodos UML

## Objetivo

Convertir cada metodo UML en un contrato funcional versionado que pueda guiar de forma determinista la generacion Spring Boot y Flutter. La firma, el comportamiento, los contratos de plataforma, la validacion y el refinamiento asistido se integran al diagrama existente sin crear un modelo paralelo.

## Documentos

1. [Modelo de especificacion](01_modelo_especificacion_metodos.md)
2. [Contratos backend y frontend](02_contratos_backend_frontend.md)
3. [Validacion y completitud](03_validacion_referencias_completitud.md)
4. [Refinamiento con IA](04_refinamiento_ia.md)
5. [Editor de especificaciones](05_editor_especificaciones.md)
6. [Modelo intermedio, XMI y versiones](06_modelo_intermedio_xmi_versiones.md)
7. [Pruebas](07_pruebas_fase4.md)
8. [Resumen](08_resumen_fase4.md)
9. [Acta de cierre](09_acta_cierre_fase4.md)

## Diagramas

- [Flujo de especificacion](diagramas/flujo_especificacion_metodo.mmd)
- [Refinamiento y confirmacion](diagramas/refinamiento_ia_confirmacion.mmd)
- [Trazabilidad hacia generadores](diagramas/trazabilidad_metodo_generadores.mmd)

## Entregables implementados

- CRUD de parametros de metodo y especificacion funcional.
- Revision optimista mediante `ETag`, `If-Match` e `If-None-Match`.
- Contratos Pydantic y TypeScript cerrados y equivalentes.
- Validacion en modo borrador y modo estricto con diagnosticos accionables.
- Refinamiento asistido como propuesta confirmable, nunca como escritura silenciosa.
- Editor integrado con cinco vistas y deteccion de cambios remotos.
- Eventos colaborativos y auditoria posterior a persistencia.
- Modelo intermedio v2 con adaptador no destructivo desde v1.
- Conservacion de parametros y especificacion en XMI y snapshots.
- Migracion Alembic reversible para la revision de especificacion.
- Pruebas de backend y frontend incorporadas a las suites existentes.

