# Fase 6 - Integracion IA local preparada

## Alcance

Se preparo el motor UML para recibir fuentes de generacion:

- Texto.
- Voz convertida a texto.
- Imagen procesada a descripcion.

## Endpoint

```text
POST /api/v1/uml/generate
```

Entrada:

- `project_id`
- `name`
- `prompt`
- `source_type`

## Funcionamiento

El motor `text_parser.py` interpreta instrucciones de dominio y crea:

- Clases candidatas.
- Atributos base.
- Metodos base.
- Relaciones secuenciales.
- Posiciones visuales iniciales.

## Decision tecnica

La fase deja un motor determinista local y extensible. La integracion con modelos IA especializados offline se conecta en fases posteriores sin modificar el contrato del editor ni del backend.
