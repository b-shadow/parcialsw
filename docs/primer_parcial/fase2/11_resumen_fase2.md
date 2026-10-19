# Fase 2 - Resumen de avance

## Que se implemento

- Analisis formal del problema y alcance del sistema.
- Definicion de actores principales y secundarios.
- Requerimientos funcionales organizados por los cuatro paquetes del sistema.
- Requerimientos no funcionales de rendimiento, seguridad, disponibilidad, escalabilidad, compatibilidad e IA offline.
- Casos de uso CU-01 a CU-18 detallados.
- Arquitectura logica de frontend, backend, motor UML, IA y generadores.
- Arquitectura fisica local y candidata para despliegue AWS.
- Arquitectura de componentes por paquete funcional.
- Flujos principales de autenticacion, proyectos, colaboracion UML, IA, XMI y generacion.
- Matriz de trazabilidad entre requisitos, casos de uso, modulos y componentes.
- Diagramas Mermaid de arquitectura general, componentes, despliegue, paquetes, WebSocket y flujo general.

## Archivos creados o modificados

- `docs/fase2/00_indice_fase2.md`
- `docs/fase2/01_analisis_del_sistema.md`
- `docs/fase2/02_actores_y_roles.md`
- `docs/fase2/03_requerimientos_funcionales.md`
- `docs/fase2/04_requerimientos_no_funcionales.md`
- `docs/fase2/05_casos_de_uso.md`
- `docs/fase2/06_arquitectura_logica.md`
- `docs/fase2/07_arquitectura_fisica.md`
- `docs/fase2/08_arquitectura_componentes.md`
- `docs/fase2/09_flujos_principales.md`
- `docs/fase2/10_matriz_trazabilidad.md`
- `docs/fase2/11_resumen_fase2.md`
- `docs/fase2/12_acta_cierre_fase2.md`
- `docs/fase2/diagramas/arquitectura_general.mmd`
- `docs/fase2/diagramas/componentes.mmd`
- `docs/fase2/diagramas/despliegue.mmd`
- `docs/fase2/diagramas/paquetes.mmd`
- `docs/fase2/diagramas/comunicacion_websocket.mmd`
- `docs/fase2/diagramas/flujo_general_sistema.mmd`

## Decisiones tecnicas tomadas

- Mantener CU-01 a CU-18 como trazabilidad funcional principal.
- Definir roles globales separados de roles internos de proyecto.
- Confirmar que el creador de un proyecto queda como Organizador interno.
- Definir WebSocket por proyecto como base de colaboracion.
- Definir el modelo UML interno como fuente de verdad para XMI, IA y generacion.
- Mantener IA final local offline como restriccion no funcional obligatoria.
- Mantener generadores Spring Boot y Flutter como procesos deterministas con asistencia opcional de IA.

## Cambios realizados en arquitectura o base de datos

- No se modifico codigo funcional de aplicacion.
- No se crearon tablas ni migraciones.
- Se formalizaron vistas logica, fisica y de componentes.
- Se establecio la trazabilidad que guiara el diseno de base de datos de Fase 3.

## Pendientes para la siguiente fase

- Disenar modelo conceptual de base de datos.
- Disenar modelo logico y fisico PostgreSQL.
- Definir diccionario de datos.
- Definir normalizacion.
- Preparar SQL inicial, entidades ORM y estrategia de migraciones.

