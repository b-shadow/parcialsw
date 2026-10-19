# Fase 3 - IA colaborativa y memoria compartida

## Objetivo

Convertir el motor unico de la fase 2 en un asistente compartido por proyecto: todos los miembros autorizados observan la misma conversacion, autores, propuestas, recomendaciones, presencia y cambios en tiempo real, con recuperacion determinista despues de una desconexion.

## Documentos

1. [Arquitectura colaborativa](01_arquitectura_colaborativa_ia.md)
2. [Protocolo WebSocket](02_protocolo_websocket.md)
3. [Memoria, resumen y contexto](03_memoria_resumen_contexto.md)
4. [Acciones y recomendaciones](04_acciones_recomendaciones.md)
5. [Interfaz del asistente de proyecto](05_interfaz_asistente_proyecto.md)
6. [Pruebas multiusuario](06_pruebas_multiusuario.md)
7. [Resumen y cierre](07_resumen_fase3.md)

## Resultado

- Una conversacion persistente por proyecto con secuencia propia.
- Identidad visible del autor y paginacion bidireccional.
- Eventos persistentes posteriores al commit y eventos efimeros de presencia/proceso.
- Cliente con heartbeat, reconexion exponencial, deduplicacion y catch-up REST.
- Memoria corta y resumen estructurado de largo plazo sin borrar mensajes.
- Acciones confirmables y recomendaciones con estados compartidos.
- Ventana de IA del proyecto separada del asistente manual global.

## Estado

Fase terminada y verificada mediante suites backend, motor IA y frontend.
