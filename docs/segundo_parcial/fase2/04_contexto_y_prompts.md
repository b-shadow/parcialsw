# Contexto y prompts

## Contexto autorizado

`ProjectContextBuilder` se ejecuta despues de validar la membresia. Solo incorpora:

- ID, nombre y descripcion del proyecto solicitado.
- ID, nombre visible, rol y permisos permitidos del actor.
- Diagrama activo que pertenece al proyecto.
- Clases, atributos, metodos, parametros y relaciones del diagrama.
- Version logica actual.
- Mensajes recientes de la conversacion del proyecto.
- Resumen disponible.
- Metadatos de versiones cuando se solicitan expresamente.
- Restricciones de idioma, trabajo local y confirmacion.

No se incorporan correos, hashes, JWT, variables de entorno, credenciales ni datos de otros proyectos.

## Presupuesto

`ContextBudget` serializa el contrato y aplica un limite de caracteres. La reduccion es determinista:

1. Elimina versiones menos prioritarias.
2. Elimina mensajes mas antiguos.
3. Retira descripcion y metadatos secundarios del diagrama.
4. Rechaza con `context_too_large` si aun excede el limite.

Nunca corta una cadena JSON a mitad. El resultado informa `context_reduced`.

## Sanitizacion

`sanitize_context_data` elimina claves relacionadas con contrasenas, secretos, tokens, autorizacion, claves privadas, VAPID y URL de base de datos. El texto redacta patrones sensibles y bytes nulos.

## Prompt por capas

1. Reglas inmutables desde `prompts/unified_system.md`.
2. JSON Schema obligatorio.
3. Contexto autorizado delimitado como no confiable.
4. Intenciones preclasificadas delimitadas.
5. Solicitud del usuario delimitada.

El prompt obliga a preservar elementos no mencionados, utilizar IDs existentes, pedir aclaracion, separar respuesta/acciones/recomendaciones y no afirmar ejecucion antes de confirmacion.

## Inyeccion de instrucciones

El contexto UML y la solicitud nunca se concatenan como instrucciones privilegiadas. Solicitudes para revelar prompts, `.env`, tokens o claves producen una negativa determinista sin consultar herramientas ni crear acciones.
