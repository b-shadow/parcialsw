# Fase 8 - Arquitectura del generador Spring Boot

## Objetivo

Convertir modelos UML internos en un proyecto backend Spring Boot funcional, exportable y compilable.

## Estructura implementada

```text
backend/app/modules/generacion_software/backend_generator/
  uml_parser/
  analyzer/
  templates/
  generator/
  validators/
  exporter/
  services/
```

## Responsabilidades

- `uml_parser`: entrada desde modelo intermedio UML.
- `analyzer`: conversion a entidades Java, campos y relaciones.
- `templates`: plantillas Spring Boot, JPA, DTO, CRUD, seguridad y excepciones.
- `generator`: escritura fisica de archivos.
- `validators`: validacion estructural previa.
- `exporter`: checksums y ZIP.
- `services`: orquestacion del generador.

## Decision tecnica

La generacion base es determinista por reglas. El motor IA local de Fase 7 aporta plan y recomendaciones, pero la salida Spring Boot no depende de APIs externas.
