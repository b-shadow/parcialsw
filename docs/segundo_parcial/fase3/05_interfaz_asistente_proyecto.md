# Interfaz del asistente de proyecto

## Separacion funcional

`AssistantWidget` sigue siendo el manual global del sistema. `ProjectAiAssistant` aparece unicamente dentro de una ruta de proyecto y trabaja con su conversacion, contexto y permisos. Ambos controles son independientes y tienen posiciones distintas.

## Comportamiento

- Encabezado con conectividad y cantidad de miembros presentes.
- Timeline cronologico con nombre del autor.
- Carga inicial de 50 mensajes y boton para paginas anteriores.
- Indicador de procesamiento compartido.
- Propuestas de accion con estado, aplicar y rechazar.
- Compositor multiliena: Enter envia y Shift+Enter crea nueva linea.
- Borrador por proyecto en `localStorage`.
- Si falla el envio, el texto vuelve al compositor.
- Al abrir, la vista avanza al mensaje reciente.

## Estado

El store Zustand conserva mensajes, acciones, recomendaciones, presencia, cursores y estado del socket. Sus reducers son idempotentes: fusionan por ID, ordenan mensajes por secuencia y usan `max` para impedir retrocesos por eventos fuera de orden.

## Contexto de diagrama

Cuando la ruta contiene `/uml/{diagram_id}`, la consulta envia ese ID y el cliente comunica `ACTIVE_DIAGRAM`. De esta forma instrucciones como “conecta esta clase” se interpretan sobre el diagrama abierto, sin crear otro modelo accidentalmente.

## Accesibilidad y adaptacion

La ventana usa `aria-label`, `aria-live`, titulos en controles de icono, foco nativo y dimensiones limitadas al viewport. En escritorio no tapa el manual global; en pantallas estrechas conserva margen lateral y desplazamiento interno.
