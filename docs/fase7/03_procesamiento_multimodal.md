# Fase 7 - Procesamiento multimodal

## Texto

Endpoint:

```text
POST /api/v1/ai/uml/text
```

Procesa instrucciones en lenguaje natural y genera clases, atributos, metodos y relaciones.

## Voz

Endpoint:

```text
POST /api/v1/ai/uml/voice
```

Recibe transcripcion o audio codificado. La fase incluye normalizacion local de transcripcion y contrato estable para integrar Whisper o Vosk local.

## Imagen

Endpoint:

```text
POST /api/v1/ai/uml/image
```

Recibe descripcion, nombre de archivo o imagen codificada. La fase incluye procesamiento local por descripcion y contrato estable para integrar OCR/vision offline.

## Salida comun

Cada modalidad devuelve:

- Clases UML.
- Relaciones UML.
- Confianza.
- Observaciones.
- Motor usado.
