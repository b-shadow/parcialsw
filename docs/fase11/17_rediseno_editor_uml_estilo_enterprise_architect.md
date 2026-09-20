# Rediseño del editor UML estilo Enterprise Architect

## Qué se implementó

- Se rediseñó el editor UML para acercarlo al flujo de herramientas como Enterprise Architect: canvas central, inspector lateral y bandeja inferior de propiedades.
- Las clases ahora se muestran con compartimentos UML separados para nombre, atributos y métodos.
- Se corrigió el movimiento de clases en el canvas: al soltar un nodo, la posición se actualiza en el estado local y se persiste mediante el endpoint de elementos visuales.
- Se reemplazó la creación fija de relaciones por un formulario explícito con origen, destino, tipo y etiqueta.
- Se añadieron tipos de relación UML: asociación, herencia, implementación, dependencia, agregación y composición.
- Los atributos y métodos se editan en tablas inferiores, con columnas de visibilidad, nombre, tipo/retorno, requerido y acciones.
- Se mantuvieron las funciones existentes de validación, importación/exportación XMI, generación por texto, voz e imagen.
- Se ajustó el toolbar del editor para modo claro y modo oscuro.
- Se agregó un toolbox lateral derecho con acciones similares al panel de Enterprise Architect: `Class`, `Associate`, `Generalize` y `Association Class`.
- El nombre de la clase ahora se puede editar directamente desde el encabezado del nodo en el canvas.
- La creación de relaciones ahora funciona por modo de herramienta: se selecciona la herramienta, luego la clase origen y luego la clase destino.
- Al seleccionar una línea se pueden editar etiqueta y multiplicidades de ambos extremos, por ejemplo `0..1`, `1`, `0..*` o `1..*`.
- La tabla inferior de atributos se simplificó a nombre, tipo y alcance público/privado.
- Se reforzaron estilos de modo oscuro/modo claro en botones, inputs, toolbar, canvas, toolbox y paneles de propiedades.
- Se corrigió el conflicto donde el editor UML seguía tomando estilos oscuros en modo claro por reglas globales de React Flow y clases `dark:` heredadas.
- Se sincronizó el tema desde `App.tsx` para que la clase `dark` del documento siempre coincida con el estado global del toggle.
- Se agregó un scope de tema propio para el editor UML, con overrides claros para canvas, controles de React Flow, inputs, textareas y selects.
- Se eliminó el panel lateral de clase seleccionada porque el nombre se edita y guarda directamente desde el nodo.
- Se retiraron acciones duplicadas en la derecha: dictado/subida de imagen separados, importación XMI pegada y exportación JSON rápida.
- El panel IA quedó con tres acciones claras: `Texto`, `Voz` e `Imagen a UML`.
- La validación dejó de ocupar espacio fijo en la derecha y ahora se muestra en una ventana flotante al pulsar `Validar`.
- La creación de clases quedó concentrada en el toolbox derecho; el toolbar superior mantiene validación, importación/exportación XMI e imagen a UML.
- Se corrigió `Association Class` para que represente la notación UML esperada: asociación principal entre dos clases y línea punteada hacia la clase asociativa.
- La tecla `Delete/Supr` elimina la clase o relación seleccionada, excepto cuando el foco está en un input, textarea o select.
- Se corrigió el borrado real de clases asociativas: ahora también se eliminan las relaciones que apuntan a la clase mediante `metadata_json.association_class_id`.
- Se actualizó el store frontend para limpiar relaciones conectadas o asociadas cuando se elimina una clase.
- `Validar` ahora refresca el modelo desde backend antes de calcular resultados, por lo que un lienzo vacío valida como modelo vacío real y no conserva elementos eliminados.
- Los atributos ahora usan tipos orientados a Spring Boot/Java mediante selector: `String`, `Integer`, `Long`, `Double`, `BigDecimal`, `Boolean`, `Character`, `LocalDate`, `LocalDateTime` y `UUID`.
- La clase asociativa generada incluye un atributo inicial `Long` para que el generador backend reciba un tipo Java consistente.
- Se migró el canvas de diagramación desde React Flow hacia JointJS (`@joint/core`) para acercar la experiencia a una herramienta CASE/UML.
- Se retiró `reactflow` de las dependencias del frontend y se eliminaron los componentes anteriores basados en nodos/aristas React Flow.
- El nuevo canvas JointJS renderiza clases UML con compartimentos, relaciones UML, etiquetas, multiplicidades, generalización y clase asociativa.
- Importación XMI, generación por texto, generación por voz, imagen a UML y generación backend se mantienen sobre el mismo modelo persistido de clases, atributos, métodos y relaciones.

## Archivos creados o modificados

- `frontend/src/modules/modelado_uml_inteligente/pages/UmlEditorPage.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/UmlClassNode.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/UmlToolbar.tsx`
- `frontend/src/modules/modelado_uml_inteligente/services/umlService.ts`
- `frontend/src/modules/modelado_uml_inteligente/store/umlStore.ts`
- `frontend/src/modules/modelado_uml_inteligente/components/UmlToolbar.tsx`
- `frontend/src/modules/modelado_uml_inteligente/components/JointUmlCanvas.tsx`
- `backend/app/modules/modelado_uml/repositories/uml_repository.py`
- `frontend/src/shared/components/Button.tsx`
- `frontend/src/shared/components/Input.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/package.json`
- `frontend/package-lock.json`
- `docs/fase11/17_rediseno_editor_uml_estilo_enterprise_architect.md`

## Decisiones técnicas tomadas

- Se conservó React Flow como motor del canvas porque ya estaba integrado y permite arrastre, nodos personalizados, minimapa, controles y aristas configurables.
- Se priorizó una experiencia de modelado más cercana a Enterprise Architect sin introducir una dependencia pesada de diagramación que obligue a reescribir el editor.
- La edición fina de miembros se movió a una bandeja inferior tipo propiedades para evitar mezclar edición de tablas dentro del nodo arrastrable.
- Las relaciones se crean desde un formulario controlado para evitar conexiones accidentales y soportar tipos UML de forma explícita.
- La posición del nodo se actualiza de forma optimista en el store local y luego se reemplaza por la respuesta persistida del backend.
- Se usó multiplicidad porque forma parte de las asociaciones en diagramas de clase UML y el modelo de persistencia ya contaba con `source_cardinality` y `target_cardinality`.
- `Association Class` se resuelve en esta etapa creando una clase intermedia y dos asociaciones enlazadas, manteniendo compatibilidad con el modelo backend existente.
- Para evitar inconsistencias visuales, el tema ya no depende solamente de clases utilitarias dispersas: el documento se sincroniza desde el estado global y el editor UML tiene un scope visual explícito.
- `Association Class` se modela sin cambiar la base de datos: la relación principal guarda `metadata_json.association_class_id` y JointJS dibuja la línea punteada hacia esa clase.
- Se restringieron los tipos de atributo a tipos Java usados por Spring Boot para reducir ambigüedad en la generación de entidades, DTOs y campos.
- La migración se limitó a la capa visual del editor. No se modificaron los endpoints ni el modelo de datos usado por el generador Spring Boot/Flutter.
- La eliminación debe limpiar persistencia y estado local; no basta con ocultar elementos del canvas porque validación y generación consumen el modelo persistido.

## Cambios de arquitectura o base de datos

- No hubo cambios de base de datos.
- No hubo cambios de contratos backend.
- El cambio es de interacción y presentación frontend sobre los endpoints existentes de clases, atributos, métodos, relaciones y elementos visuales.
- Se reutilizó el contrato existente de relaciones para actualizar etiqueta y multiplicidades.

## Pendientes para la siguiente fase

- Añadir conectores manuales por arrastre entre puertos si se decide habilitar conexiones directas en canvas.
- Mejorar la notación visual de agregación/composición con marcadores de diamante personalizados.
- Añadir propiedades avanzadas de operaciones como parámetros, estereotipos y multiplicidad.

## Verificación

- `npm run build`
- `npm test -- --run`

## Correccion de render del canvas JointJS

- Se rastreo el flujo completo de creacion de clases: `Class` llama a `handleAddClass`, el backend persiste la clase y `Validar` la encontraba en el modelo, pero el canvas no la mostraba.
- La causa no estaba en la persistencia ni en el validador. El problema era de ciclo de vida frontend: JointJS se habia montado sobre el mismo `div` que React controla como raiz del canvas.
- En desarrollo, `React.StrictMode` ejecuta montaje y limpieza del efecto. Durante esa limpieza, `paper.remove()` eliminaba el `el` recibido por JointJS, que era el contenedor principal de React para el canvas.
- Se separo el wrapper de React del host interno de JointJS: React conserva el contenedor principal y JointJS solo crea/elimina su propio SVG dentro de un `div` dedicado.
- Se agrego una capa visual sincronizada con el store UML para que las clases y relaciones persistidas tengan una representacion deterministica en el lienzo aunque el paper de JointJS se remonte.
- La migracion sigue manteniendo el mismo modelo persistido de clases, atributos, metodos y relaciones, por lo que la generacion backend Spring Boot y frontend Flutter no cambia de contrato.

## Verificacion adicional

- `npm run build`
- `npm test -- --run`
- `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_phase6_uml_engine.py`

## Navegacion del lienzo UML

- Se agrego navegacion del lienzo mediante zoom y paneo para evitar que clases ubicadas fuera del marco fijo queden inaccesibles.
- El canvas ahora maneja un viewport con `x`, `y` y `scale`, conservando las posiciones persistidas como coordenadas de mundo UML.
- Se habilito zoom con rueda del mouse y controles `+`, `-`, `100%`.
- El zoom por rueda se implemento con un listener nativo `{ passive: false }` para evitar el error del navegador `Unable to preventDefault inside passive event listener invocation`.
- Se habilito mover el lienzo arrastrando el fondo, sin interferir con el arrastre de clases.
- Se ajusto la capa interna de JointJS para no capturar eventos del espacio vacio, permitiendo desplazar el lienzo al presionar y arrastrar sobre areas sin clases.
- Tras crear una relacion con `Associate`, `Generalize` o `Association Class`, el editor vuelve automaticamente a `Select` para que las clases puedan moverse sin romper el enlace.
- Las relaciones ahora eligen automaticamente el punto de conexion mas cercano entre arriba, derecha, abajo e izquierda de cada clase, evitando que todas las lineas salgan siempre desde un mismo lado.
- Se eligio conexion automatica por distancia como primera solucion porque no requiere cambios de base de datos ni metadatos adicionales por relacion; las anclas manuales quedan como mejora futura si se necesita fijar lados especificos.
- Al eliminar una clase con `Delete/Supr`, ahora se eliminan automaticamente todas sus relaciones conectadas antes de borrar la clase.
- El backend dejo de depender de operadores JSON especificos del dialecto SQL para encontrar relaciones de clases asociativas; ahora filtra las relaciones del diagrama de forma portable.
- El borrado de clases y relaciones tambien limpia sus elementos visuales asociados para evitar restos huerfanos en el canvas.
- La grilla visual acompana el desplazamiento y escala del viewport para mantener orientacion espacial.
- El boton `Class` ahora crea siempre la clase nueva en la posicion inicial fija `{ x: 90, y: 90 }`; esto aplica solo a la creacion manual desde toolbox y no altera importacion XMI, generacion por texto, voz o imagen.

## Verificacion adicional de navegacion

- `npm run build`
- `npm test -- --run`
- `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_phase6_uml_engine.py`

## Compatibilidad XML/XMI con Enterprise Architect

- Se reviso el error de Enterprise Architect al importar el archivo generado: `Unknown XMI Exporter or Version`.
- Aunque Enterprise Architect descarga y selecciona archivos `.xml`, el contenido para intercambio UML es XMI, es decir, XML con estructura y metadatos XMI reconocibles.
- El exportador anterior generaba un XML con raiz `xmi:XMI` en estilo XMI 2.1, pero la ventana de Enterprise Architect usada como referencia trabaja con `Export Type: XMI 1.1`.
- Se ajusto el backend para descargar archivos `.xml` y emitir XML/XMI 1.1 con estructura clasica similar a Enterprise Architect: `XMI.header`, `XMI.documentation`, `XMI.content`, `UML:Model`, `UML:Class`, `UML:Association`, `UML:Generalization`, `UML:Dependency` y `UML:Abstraction`.
- Las asociaciones ahora incluyen `UML:Association.connection` con extremos `UML:AssociationEnd`, de forma mas cercana al XML exportado por EA.
- Se tomo como referencia un XML real exportado por Enterprise Architect y se acerco la salida a esa estructura: `UML:Package` dentro de `UML:Model`, clase tecnica `EARootClass`, `UML:Diagram`, `UML:Diagram.element`, `UML:DiagramElement`, `XMI.difference` y `XMI.extensions`.
- El XML exportado queda indentado para facilitar comparacion manual con archivos generados por Enterprise Architect.
- Los identificadores XMI se normalizan para evitar UUIDs o nombres con caracteres problematicos en IDs XML.
- La importacion interna se amplio para leer tanto el formato XMI 2.1 anterior como el nuevo XML/XMI 1.1 con tags `UML:*`.

## Verificacion adicional de XMI

- `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_phase6_uml_engine.py`

## Rediseno de pantalla colaborativa

- Se redisenio la pantalla colaborativa del proyecto con una composicion mas cercana a Enterprise Architect: breadcrumb superior, cabecera del proyecto, acciones de gestion/versionado, columna izquierda de creacion e importacion y panel principal de modelos disponibles.
- La pantalla ahora contempla modo claro y modo oscuro con fondos, bordes, tarjetas, buscador, selector y estados contrastados.
- Se agrego busqueda local de diagramas y filtro por tipo usando los tipos reales disponibles en `diagram_type`.
- Las tarjetas de modelos muestran solo informacion disponible: nombre, descripcion, tipo, version, estado, fecha de creacion y usuario creador identificado por iniciales del `created_by_user_id`.
- Las acciones de cada modelo son `Editar` y `Eliminar`; se retiro la accion visual `Ver`.
- Se agrego eliminacion real de diagramas en backend con `DELETE /api/v1/uml/diagrams/{diagram_id}`.
- El borrado de diagrama limpia elementos visuales e intercambios XML asociados antes de eliminar el diagrama.

## Verificacion adicional de colaborativo

- `npm run build`
- `npm test -- --run`
- `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_phase6_uml_engine.py -q`

## Importacion XML real de Enterprise Architect

- Se valido el archivo `exportar.xml` generado por Enterprise Architect desde un paquete `clases` con un unico `ClassDiagram`.
- El importador ahora usa el `UML:Diagram` con `diagramType="ClassDiagram"` como filtro de verdad para importar solo los elementos presentes en ese diagrama.
- Se extraen clases UML reales y se ignora la clase tecnica `EARootClass`.
- Se leen atributos y operaciones de EA aunque el tipo venga en `UML:TaggedValue tag="type"` en vez de como atributo directo.
- Se importan posiciones visuales desde `UML:DiagramElement geometry="Left=...;Top=...;Right=...;Bottom=...;"`.
- Se importan asociaciones aunque los conectores no tengan coordenadas de caja, porque ahora los subjects de conectores tambien cuentan como elementos del diagrama.
- Se conservan multiplicidades de `UML:AssociationEnd multiplicity`.
- Se detecta la clase asociativa de Enterprise Architect mediante `UML:TaggedValue tag="associationclass"` y al persistir se remapea al UUID interno para que el editor pueda dibujar la relacion asociativa.

## Verificacion adicional de importacion EA

- Importacion directa de `C:\Users\LENOVO\Downloads\exportar.xml`: `clases`, 4 clases, 2 asociaciones, posiciones y multiplicidades leidas correctamente.
- `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_phase6_uml_engine.py -q`
- `npm run build`
- `npm test -- --run`
