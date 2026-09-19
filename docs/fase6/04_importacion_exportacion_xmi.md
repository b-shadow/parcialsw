# Fase 6 - Importacion y exportacion XMI

## Exportacion

Endpoint:

```text
GET /api/v1/uml/diagrams/{diagram_id}/xmi
```

Genera un documento XML con:

- Namespace XMI.
- Namespace UML.
- Modelo.
- Clases.
- Atributos.
- Operaciones.
- Relaciones.

## Importacion

Endpoint:

```text
POST /api/v1/uml/xmi/import
```

Procesa contenido XMI y crea un diagrama editable persistido.

## Trazabilidad

Cada intercambio se registra en `xmi_exchanges` con:

- Diagrama.
- Usuario.
- Tipo de intercambio.
- Herramienta.
- Archivo.
- Estado.
- Metadatos.

## Compatibilidad

El formato usa etiquetas UML comunes como `packagedElement`, `ownedAttribute` y `ownedOperation`, manteniendo compatibilidad conceptual con herramientas externas como Enterprise Architect.
