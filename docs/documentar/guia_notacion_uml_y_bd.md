# Guia de notacion para documentar diagramas

Este documento resume la notacion que se usara para dibujar en Enterprise Architect los diagramas de los casos de uso del sistema CASE Inteligente. Se excluye CU07 porque el asistente/manual guiado todavia no esta cerrado funcionalmente.

## Reglas UML usadas

- Diagrama de clases: usar clases con compartimentos de nombre, atributos y metodos. Mostrar asociaciones, dependencias, generalizaciones y multiplicidades cuando el caso de uso las necesite.
- Diagrama de secuencia: usar un marco `sd CUXX Nombre`, actor a la izquierda, lifelines por capa y mensajes de arriba hacia abajo. Las respuestas se dibujan punteadas.
- Diagrama de estado: usar estado inicial, estados con nombre, transiciones con evento y estado final cuando el flujo termina. Es util para modelar ciclos de vida de sesion, proyecto, diagrama, transformacion y artefactos.
- Diagrama de comunicacion: usar objetos conectados por enlaces y mensajes numerados (`1`, `1.1`, `2`). Sirve para ver que objetos colaboran, no para enfatizar tiempo vertical.
- Diagrama de base de datos: usar entidades/tablas como rectangulos con nombre y atributos. Para este trabajo se listan atributos sin tipo de dato, como pide el criterio del documento; las relaciones llevan cardinalidad conceptual.

## Criterios del sistema

- Las clases de frontera se nombran como `Frontend::<Pagina o Servicio>`.
- Las clases/controladores backend se nombran como `API::<Router>`.
- Las clases de negocio se nombran como `Servicio::<Service>`.
- Las clases de persistencia se nombran como `Repo::<Repository>`.
- Las entidades se nombran con el modelo ORM real: `User`, `Project`, `UmlDiagram`, `UmlClass`, `UmlTransformation`, etc.
- No se dibujan validaciones internas repetitivas si el diagrama se vuelve demasiado cargado.
- No se dibujan controles visuales concretos como botones o inputs; se documenta la responsabilidad funcional.

## Fuentes consultadas

- OMG UML 2.5.1: https://www.omg.org/spec/UML/2.5.1/About-UML
- UML diagrams overview: https://www.uml-diagrams.org/uml-25-diagrams.html
- ERD conceptual: https://lucid.co/diagram/erd/tutorial
- ERD con atributos con o sin tipo: https://www.red-gate.com/blog/symbol-in-erd-diagram/
