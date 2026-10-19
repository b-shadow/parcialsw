# Fase 6 - Motor UML y modelo interno

## Objetivo

Definir un modelo interno UML independiente de la interfaz grafica y de la persistencia SQLAlchemy.

## Implementacion

Se creo `backend/app/modules/modelado_uml/engine/`.

Componentes:

- `internal_model.py`: representacion interna serializable.
- `text_parser.py`: generacion determinista de UML desde instrucciones.
- `validator.py`: validacion estructural y recomendaciones.
- `xmi.py`: importacion y exportacion XMI.

## Modelo interno

El modelo interno representa:

- Diagrama UML.
- Clase UML.
- Atributo UML.
- Metodo UML.
- Parametro UML.
- Relacion UML.
- Elemento visual.

## Decision tecnica

Se uso Pydantic para el modelo interno porque permite validacion, serializacion y compatibilidad directa con FastAPI sin acoplar el motor a React Flow ni a SQLAlchemy.
