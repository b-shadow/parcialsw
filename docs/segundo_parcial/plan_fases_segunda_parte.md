# Plan de fases de la segunda parte

## 1. Objetivo general

La segunda parte ampliara CASE Inteligente sobre la base funcional construida en el primer parcial. El objetivo es completar la personalizacion del frontend generado, incorporar generacion funcional basada en la descripcion de metodos, convertir la IA en un asistente integral y colaborativo por proyecto, consolidar el versionado y ofrecer una experiencia movil reducida para consulta y notificaciones.

Las fases descritas en este documento son divisiones tecnicas para controlar dependencias, pruebas y riesgos. Todas forman parte de una sola implementacion integral y deben quedar conectadas y funcionando en conjunto antes de considerar terminada la segunda parte.

## 2. Principios de implementacion

- Reutilizar el editor UML, los generadores, WebSocket, versionado, notificaciones y previsualizacion ya existentes.
- Mantener contratos compartidos entre React, FastAPI, el motor de IA, Spring Boot generado y Flutter generado.
- Procesar las respuestas de IA como acciones estructuradas y validadas, no como escrituras directas en la base de datos.
- Exigir confirmacion para acciones destructivas o de alto impacto.
- Mantener el funcionamiento local mediante Ollama y Qwen, con el motor de reglas como respaldo.
- Generar Spring Boot y Flutter desde un mismo modelo funcional intermedio.
- Incorporar pruebas y validaciones dentro de cada fase, aunque la entrega sea unica.

## 3. Base existente que se aprovechara

La implementacion parte de las siguientes capacidades ya desarrolladas:

- Creacion y edicion de diagramas UML.
- Generacion UML mediante texto, voz e imagen.
- Modificacion de diagramas existentes mediante lenguaje natural.
- Colaboracion en tiempo real mediante WebSocket.
- Guardado manual y restauracion controlada de versiones.
- Generacion de backend Spring Boot y frontend Flutter.
- Previsualizacion inicial y configuracion de estilos Flutter.
- Notificaciones Web Push.
- Asistente flotante de ayuda del sistema.

## 4. Fase 1: contratos, persistencia y migraciones

### Objetivo

Definir primero los datos compartidos que necesitaran el resto de las fases para evitar incompatibilidades entre modulos.

### Trabajo

- Extender el modelo UML para almacenar la especificacion funcional de los metodos.
- Crear persistencia para conversaciones, mensajes, acciones y recomendaciones de IA por proyecto.
- Crear persistencia para la configuracion visual Flutter por proyecto.
- Definir contratos para solicitudes de IA con una o varias intenciones.
- Definir eventos WebSocket para mensajes, propuestas, acciones y resultados de IA.
- Ampliar los snapshots de version para incluir configuracion visual y de generacion.
- Preparar migraciones reversibles y compatibles con los datos existentes.
- Definir contratos de consulta movil en modo lectura.

### Resultado esperado

Frontend, backend, IA y generadores utilizan estructuras compatibles y versionadas.

### Criterios de cierre

- Las migraciones se aplican y revierten correctamente.
- Los contratos aparecen en OpenAPI.
- Los datos existentes siguen siendo validos.
- Las pruebas de serializacion y persistencia quedan aprobadas.

## 5. Fase 2: motor unico de IA con Ollama y Qwen

### Objetivo

Implementar una sola IA capaz de adaptar su comportamiento a lo que solicita el usuario, sin personalidades separadas.

### Trabajo

- Integrar un proveedor local Ollama con un modelo Qwen apropiado para los recursos disponibles.
- Mantener el motor de reglas actual como fallback cuando Ollama no este disponible.
- Detectar una o varias intenciones dentro de una misma solicitud.
- Diferenciar consultas, explicaciones, recomendaciones, validaciones, modificaciones UML, generacion y resumen.
- Recuperar contexto del proyecto, usuario, diagrama activo, versiones y conversacion.
- Generar planes de acciones estructurados en JSON.
- Validar cada accion antes de ejecutarla.
- Reintentar o rechazar respuestas malformadas.
- Solicitar confirmacion antes de aplicar eliminaciones, restauraciones o cambios extensos.

### Flujo principal

```text
Usuario autenticado
    -> deteccion de proyecto y diagrama
    -> clasificacion de intenciones
    -> construccion de contexto
    -> plan de acciones
    -> validacion de permisos y estructura
    -> ejecucion mediante servicios internos
    -> validacion del resultado
    -> persistencia y respuesta
```

### Resultado esperado

La IA puede explicar, recomendar, moderar, modificar, generar y revisar segun la solicitud recibida, usando una sola conversacion y un solo motor logico.

### Criterios de cierre

- Funciona con Ollama disponible.
- El sistema continua funcionando con el fallback local.
- Las respuestas invalidas no modifican datos.
- Las solicitudes compuestas producen acciones ordenadas.
- Los permisos del usuario se respetan en todas las acciones.

## 6. Fase 3: IA colaborativa y memoria por proyecto

### Objetivo

Permitir que todos los colaboradores autorizados interactuen con la misma IA y compartan el contexto del proyecto.

### Trabajo

- Mantener una conversacion compartida por proyecto.
- Identificar automaticamente al usuario mediante su sesion autenticada.
- Guardar preguntas, respuestas, recomendaciones y acciones ejecutadas.
- Transmitir mensajes y resultados mediante WebSocket.
- Mostrar quien realizo cada consulta.
- Permitir que la IA consulte el diagrama actualmente abierto.
- Crear resumenes periodicos para evitar cargar todo el historial al modelo.
- Registrar referencias a clases, relaciones, metodos y versiones.
- Incorporar estados de accion: propuesta, confirmada, aplicada, rechazada o fallida.
- Notificar a los colaboradores cuando exista una recomendacion o cambio relevante.

### Resultado esperado

La IA se comporta como un integrante unico del proyecto: entiende el contexto compartido, reconoce quien pregunta y conserva la continuidad de la conversacion.

### Criterios de cierre

- Dos usuarios conectados observan la misma conversacion en tiempo real.
- Cada mensaje conserva autor, fecha y proyecto.
- Una reconexion recupera el historial sin duplicar mensajes.
- Las acciones repetidas no se ejecutan dos veces.
- Un usuario sin acceso al proyecto no puede consultar su conversacion.

## 7. Fase 4: especificacion funcional de metodos

### Objetivo

Convertir las descripciones de los metodos UML en especificaciones estructuradas que puedan utilizar ambos generadores.

### Datos de un metodo

- Nombre.
- Descripcion funcional.
- Parametros y tipos.
- Tipo de retorno.
- Precondiciones.
- Postcondiciones.
- Reglas de negocio.
- Validaciones.
- Efectos secundarios.
- Permisos requeridos.
- Entidades relacionadas.
- Exposicion publica o uso interno.

### Trabajo

- Ampliar el editor de propiedades de metodos.
- Permitir que la IA complete o refine la especificacion desde lenguaje natural.
- Validar referencias a clases, atributos y relaciones existentes.
- Inferir el tipo de operacion: consulta, creacion, actualizacion, eliminacion, calculo o accion de negocio.
- Determinar si el metodo requiere endpoint y representacion visual.
- Guardar la especificacion dentro del modelo intermedio.
- Conservar la informacion al importar, exportar y versionar cuando el formato lo permita.

### Resultado esperado

Cada metodo funcional posee informacion suficiente para generar comportamiento consistente en backend y frontend.

### Criterios de cierre

- Las descripciones incompletas producen advertencias claras.
- Las referencias inexistentes se rechazan.
- Los metodos internos quedan diferenciados de las acciones visibles.
- La especificacion permanece estable al guardar y volver a abrir el diagrama.

## 8. Fase 5: generacion coordinada Spring Boot y Flutter

### Objetivo

Aplicar la especificacion de los metodos tanto al backend Spring Boot como al frontend Flutter generado.

### Generacion Spring Boot

- Servicios y operaciones de negocio.
- Endpoints REST cuando el metodo sea publico.
- DTO de entrada y respuesta.
- Validaciones y reglas de negocio.
- Consultas a repositorios y relaciones.
- Excepciones controladas.
- Autorizacion cuando este especificada.
- Pruebas unitarias iniciales.

### Generacion Flutter

- Botones y acciones asociados a los metodos visibles.
- Formularios segun parametros y tipos.
- Selectores para referencias a otras entidades.
- Calendarios para fechas.
- Controles numericos, booleanos y de texto adecuados.
- Filtros para metodos de consulta.
- Llamadas al endpoint Spring Boot correspondiente.
- Estados de carga, exito y error.
- Actualizacion de listas y detalles despues de una operacion.

### Regla central

Ningun metodo funcional se transformara solamente en backend sin evaluar su representacion Flutter. Solo se omitira la interfaz cuando la especificacion indique expresamente que el metodo es interno.

### Resultado esperado

Spring Boot y Flutter comparten rutas, DTO, parametros, validaciones y comportamiento derivados del mismo contrato.

### Criterios de cierre

- El backend generado compila.
- Flutter supera analisis estatico y compilacion de prueba.
- Las rutas consumidas por Flutter existen en Spring Boot.
- Los tipos y nombres coinciden en ambos proyectos.
- Las reglas principales tienen pruebas generadas.

## 9. Fase 6: editor visual y previsualizacion Flutter

### Objetivo

Completar el editor de estilos para que la previsualizacion represente fielmente el frontend que se descargara.

### Trabajo

- Persistir el tema por proyecto.
- Construir el preview con entidades y metodos reales del diagrama.
- Previsualizar lista, detalle, formulario y acciones de negocio.
- Editar colores, tipografia, botones, campos, tarjetas y navegacion.
- Incorporar temas claro y oscuro.
- Guardar y reutilizar presets personalizados.
- Validar contraste, textos largos y desbordamientos.
- Compartir una sola normalizacion de estilos entre preview y generador.
- Incluir el tema dentro de las versiones del proyecto.

### Resultado esperado

La apariencia, controles y acciones mostrados en el preview coinciden con el proyecto Flutter generado.

### Criterios de cierre

- Cada propiedad visual soportada afecta al preview y al ZIP.
- No existen controles simulados que falten en el proyecto generado.
- El preview funciona en escritorio y resoluciones moviles.
- Las configuraciones invalidas vuelven a valores seguros.

## 10. Fase 7: versionado, bitacora y notificaciones

### Objetivo

Integrar los cambios de UML, IA, estilos y generacion dentro del control de versiones y la trazabilidad del proyecto.

### Trabajo

- Mantener el guardado manual de versiones.
- Incluir diagramas, estilos y configuracion de generacion en cada snapshot.
- Crear una copia de seguridad automatica antes de restaurar.
- Restringir la restauracion al creador u organizador.
- Mantener la conversacion de IA como bitacora independiente e inmutable.
- Registrar quien creo, modifico, genero o restauro contenido.
- Emitir notificaciones por invitaciones, cambios relevantes, versiones, IA y generaciones finalizadas.
- Evitar notificaciones duplicadas o excesivas por ediciones menores.

### Resultado esperado

El proyecto puede regresar a una version guardada sin perder trazabilidad ni conversaciones posteriores.

### Criterios de cierre

- Restaurar una version recupera UML y estilos correctos.
- La restauracion no elimina la conversacion ni la bitacora.
- Usuarios sin permisos no pueden restaurar.
- Las notificaciones conducen a la pantalla relacionada.

## 11. Fase 8: aplicacion movil reducida

### Objetivo

Ofrecer una version movil informativa de CASE Inteligente para consultar proyectos y recibir novedades sin trasladar todo el editor de escritorio.

### Estrategia

Se construira un cliente Flutter en `mobile/`, orientado a Android e iOS y separado del generador de aplicaciones Flutter. Reutiliza la autenticacion, contratos REST, permisos, conversacion compartida, bitacora, versiones, notificaciones y WebSocket del backend existente. La aplicacion React conserva la experiencia completa de escritorio.

### Funciones incluidas

- Inicio de sesion.
- Lista y detalle de proyectos.
- Miembros y actividad reciente.
- Lista de diagramas.
- Visor UML de solo lectura.
- Pan, zoom y ajuste del diagrama a la pantalla.
- Consulta de versiones.
- Conversacion con la IA.
- Estado de generaciones.
- Recepcion y apertura de notificaciones.
- Cache privada por usuario para perfil, proyectos y diagramas previamente consultados.
- Reconexion WebSocket con deduplicacion de eventos.

### Funciones excluidas inicialmente

- Edicion completa del lienzo UML.
- Creacion manual compleja de relaciones.
- Administracion avanzada de usuarios.
- Restauracion de versiones.
- Operaciones pesadas de generacion desde pantallas pequenas.

### Resultado esperado

El usuario puede instalar la aplicacion Flutter, consultar sus proyectos y diagramas, conversar con la IA y revisar notificaciones desde el movil.

### Criterios de cierre

- Las pantallas funcionan en resoluciones moviles comunes.
- Los diagramas grandes pueden recorrerse sin desbordamientos.
- La interfaz oculta herramientas exclusivas de escritorio.
- Las notificaciones abren el proyecto o evento correspondiente.
- Los permisos son iguales a los de la version web.
- El APK Android compila y las pruebas Flutter pasan sin observaciones.
- La superficie `/mobile` del backend no expone operaciones mutables.

## 12. Fase 9: pruebas integrales y endurecimiento

### Objetivo

Verificar la segunda parte como un unico flujo y evitar que las nuevas capacidades rompan las funciones del primer parcial.

### Trabajo

- Pruebas unitarias de contratos, validadores y transformaciones.
- Pruebas funcionales de IA, UML, generacion y versiones.
- Pruebas concurrentes de WebSocket y conversacion compartida.
- Pruebas de permisos por rol.
- Pruebas con Ollama disponible, detenido y con respuesta invalida.
- Pruebas de solicitudes con multiples acciones.
- Pruebas de compilacion de Spring Boot generado.
- Pruebas de analisis y compilacion Flutter.
- Comparacion entre preview y configuracion generada.
- Pruebas de widgets, navegacion, cache y compilacion Flutter movil.
- Pruebas de migracion sobre una base existente.
- Revision de seguridad, secretos, archivos generados y dependencias.

### Criterios de cierre

- No existen regresiones en autenticacion, proyectos, UML o generacion anterior.
- Todos los contratos frontend/backend coinciden.
- Las operaciones colaborativas son idempotentes.
- Los proyectos generados se ejecutan con los comandos documentados.
- Los fallos del modelo de IA no corrompen diagramas ni conversaciones.
- Las pruebas automatizadas y verificaciones manuales criticas quedan aprobadas.

## 13. Orden de implementacion dentro de la pasada unica

```text
1. Contratos y migraciones
2. Proveedor Ollama/Qwen y orquestador de intenciones
3. Conversacion colaborativa y memoria por proyecto
4. Especificacion funcional de metodos
5. Generacion coordinada Spring Boot/Flutter
6. Editor de estilos y preview basado en el modelo real
7. Integracion con versiones, bitacora y notificaciones
8. Aplicacion Flutter movil de solo lectura
9. Pruebas integrales, compilacion y endurecimiento
```

Aunque exista este orden interno, no se considerara entregada una fase aislada. El resultado final debe demostrar el flujo completo desde el modelado y la conversacion con IA hasta la previsualizacion, generacion, versionado y consulta movil.

## 14. Riesgos principales y controles

| Riesgo | Control propuesto |
| --- | --- |
| Ollama no esta instalado o el modelo no cabe en memoria | Perfil Qwen configurable, comprobacion de salud y fallback de reglas |
| La IA devuelve acciones invalidas | Esquemas JSON, validacion, reintento y rechazo seguro |
| Una solicitud modifica demasiado el diagrama | Vista previa de acciones y confirmacion explicita |
| Mensajes o cambios duplicados por reconexion | Identificadores idempotentes y numeros de secuencia |
| Backend y Flutter generan contratos diferentes | Modelo funcional intermedio unico y pruebas cruzadas |
| El preview no coincide con Flutter | Configuracion compartida y pruebas de fidelidad |
| Una restauracion destruye trabajo reciente | Version de respaldo automatica y permisos de organizador |
| Diagramas grandes fallan en movil | Visor de solo lectura con pan, zoom y ajuste |
| Las notificaciones saturan al usuario | Agrupacion por evento y exclusion de cambios menores |
| Una migracion afecta datos existentes | Pruebas de upgrade, downgrade y respaldo previo |

## 15. Definicion final de terminado

La segunda parte estara terminada cuando un equipo pueda trabajar sobre un proyecto compartido, conversar con una IA unica que comprende al usuario y el contexto, describir metodos en lenguaje natural, generar Spring Boot y Flutter coherentes, personalizar y previsualizar el frontend, guardar una version, recibir notificaciones y consultar el proyecto desde un dispositivo movil sin perder las funciones construidas en el primer parcial.
