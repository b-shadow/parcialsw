# Visor UML de solo lectura

## Renderizado

`UmlReadonlyCanvas` combina:

- `InteractiveViewer` para pan y pinch-to-zoom.
- `TransformationController` para acercar, alejar y centrar.
- `CustomPainter` para relaciones, cardinalidades y terminaciones UML.
- `UmlClassCard` para nombre, estereotipo, atributos y metodos.

El lienzo calcula un area estable a partir de posiciones/tamanos persistidos. Los nodos no cambian de posicion durante gestos o al abrir detalles.

## Interaccion

- Tocar una clase abre su ficha completa.
- El boton relaciones abre una lista legible de extremos, tipo y multiplicidad.
- Las relaciones dependency/implementation usan trazo discontinuo.
- Herencia e implementacion usan triangulo.
- Agregacion/composicion usan rombo.

## Restricciones

No existen handlers de arrastre de nodos, formularios de propiedades, guardar, eliminar o crear. La prueba de widget comprueba que el modelo se muestra y que no aparecen comandos de edicion.
