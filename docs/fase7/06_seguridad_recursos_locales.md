# Fase 7 - Seguridad y recursos locales

## Seguridad

- Los endpoints IA requieren JWT.
- No se usan APIs externas durante inferencia.
- Los datos del usuario se procesan localmente.
- Las solicitudes se validan con Pydantic.
- La integracion queda dentro de los modulos funcionales existentes.

## Recursos

Perfil actual:

- CPU.
- Bajo consumo de memoria.
- Sin GPU requerida.
- Sin descarga de modelos durante ejecucion.

## Gestion futura de modelos

La arquitectura permite reemplazar el motor por:

- Ollama.
- llama.cpp.
- Transformers local.
- vLLM local.

Sin cambiar contratos externos.
