# Fase 6 - Validacion inteligente UML

## Implementacion

La validacion se centraliza en:

```text
backend/app/modules/modelado_uml/engine/validator.py
```

## Reglas

Errores:

- Diagrama sin clases.
- Clase sin nombre.
- Relacion incompleta.
- Relacion con origen inexistente.
- Relacion con destino inexistente.

Advertencias:

- Clases con nombres duplicados.
- Relaciones reflexivas.

Recomendaciones:

- Agregar atributos a clases sin estado.
- Agregar metodos a clases sin comportamiento.
- Agregar relaciones cuando hay varias clases desconectadas.

## Resultado

El endpoint `POST /api/v1/uml/diagrams/{diagram_id}/validate` devuelve errores, advertencias y recomendaciones listas para ser mostradas en el editor.
