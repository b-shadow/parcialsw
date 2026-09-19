# Pipelines Multimodales

## Texto

Entrada de lenguaje natural:

`prompt -> normalizacion -> dataset/RAG -> clases -> relaciones -> respuesta UML`

## Voz

Entrada por transcripcion o audio:

`audio/transcripcion -> normalizacion voz -> texto -> motor UML`

El flujo conserva ejecucion offline y permite integrar Whisper o Vosk local.

## Imagen

Entrada por descripcion o imagen:

`imagen/descripcion -> preprocesamiento -> OCR/deteccion preparada -> texto estructural -> motor UML`

El pipeline mantiene contratos para reconstruir clases, atributos, metodos y relaciones.

## Salida comun

Todas las modalidades devuelven:

- clases.
- atributos.
- metodos.
- relaciones.
- cardinalidades.
- confianza.
- observaciones.
- contexto de conocimiento.
