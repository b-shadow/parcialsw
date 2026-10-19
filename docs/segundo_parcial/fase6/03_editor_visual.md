# Editor visual

## Arquitectura React

`GenerationPage` conserva seleccion, transformacion y generacion. `FlutterStyleWorkspace` concentra el editor y recibe `projectId`, `transformationId`, tema y callback. Las funciones de contrato residen en `theme/themeContract.ts` y el acceso HTTP en `generationService.ts`.

El estado separa tema guardado, borrador, revision, presets, manifiesto y contexto efimero del preview. Aplicar un preset solo cambia el borrador. Cancelar vuelve al tema guardado. Guardar envia `If-Match` o `If-None-Match`; un conflicto conserva el borrador y muestra una advertencia.

## Controles

Se editan paletas claro/oscuro, modo inicial, escala y peso tipografico, variantes de boton/campo/card/navegacion, densidad y cuatro radios. La familia se muestra como `Sistema`, unica opcion realmente disponible sin assets externos. Cada color posee swatch nativo e input hexadecimal. Los errores de contraste bloquean el guardado.

La navegacion automatica usa barra inferior con 2 a 4 modulos y drawer con 0, 1 o mas de 4. Si se solicita barra con menos de dos destinos, ambos motores aplican el fallback seguro a drawer exigido por Material.

## Colaboracion

El editor escucha `FLUTTER_THEME_UPDATED`. Sin cambios locales recarga la revision confirmada; con un borrador sucio no mezcla valores y exige decision del usuario. El evento se publica despues del commit y queda en la bitacora colaborativa.
