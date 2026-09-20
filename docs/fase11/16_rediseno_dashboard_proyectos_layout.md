# Rediseño dashboard de proyectos, sidebar y topbar

## Que se implemento

- Se rediseño el layout autenticado con sidebar de navegacion mas visual.
- Se rediseño el topbar con toggle de tema y boton de cierre de sesion destacado.
- Se actualizo el toggle global para alinearse al nuevo estilo visual.
- Se rediseño la pantalla de gestion de proyectos como dashboard:
  - encabezado principal,
  - tarjetas de metricas,
  - formulario de nuevo proyecto,
  - buscador,
  - tarjetas de proyectos existentes,
  - acciones de gestionar, colaborativo y archivar.
- Se aplicaron estilos explicitos para modo claro y modo oscuro en la pantalla de proyectos.

## Archivos creados o modificados

- `frontend/src/shared/layouts/AppLayout.tsx`
- `frontend/src/shared/components/ThemeToggle.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectsPage.tsx`

## Decisiones tecnicas tomadas

- La pantalla de proyectos usa `useThemeStore` para calcular clases por modo activo y evitar estados hibridos.
- El sidebar conserva las rutas existentes y agrega una agrupacion visual de Proyectos con subopciones.
- Las metricas se calculan desde los proyectos disponibles:
  - activos,
  - archivados.
- La metrica de generaciones queda preparada visualmente, pero sin consumo de endpoint especifico por ahora.
- Los proyectos archivados muestran accion deshabilitada para evitar llamadas redundantes.

## Cambios de arquitectura o base de datos

- No hubo cambios de base de datos.
- No hubo nuevos endpoints.
- El cambio fue de experiencia de usuario y layout frontend.

## Verificacion

- `npm run build`
- `npm test`

## Refinamiento de fidelidad visual

- Se ajusto el header para evitar solapamiento entre titulo y frase lateral.
- Se agregaron clases CSS dedicadas para el grid de metricas y el grid principal del dashboard.
- Las metricas quedan en tres columnas en desktop, como el diseño de referencia, y pasan a una columna en pantallas menores a 1180px.
- El formulario y el listado usan una proporcion fija de `360px + contenido flexible` en desktop.
- Se refinaron tonos de tarjetas, bordes y paneles para modo oscuro.

## Correccion de subnavegacion de proyectos

- La opcion `Gestionar` queda activa en `/proyectos` y `/proyectos/{projectId}`.
- La opcion `Colaborativo` queda activa en `/proyectos/{projectId}/colaborativo` y en el editor UML `/proyectos/{projectId}/uml/{diagramId}`.
- Las subopciones de Proyectos apuntan al proyecto actual cuando existe un `projectId` en la URL.
- Se quito el punto decorativo de la opcion `Gestionar`.
- Se reemplazo el caracter corrupto del indicador de Proyectos por `⌃`.

## Correccion posterior de estados visuales

- La pantalla inicial `/proyectos` activa solo la opcion principal `Proyectos`, no la subopcion `Gestionar`.
- `Gestionar` queda activa exclusivamente en `/proyectos/{projectId}`.
- Se corrigio el hover del sidebar para que en modo claro no use apariencia oscura.
- Se ajusto el toggle global para que el modo claro tenga pista clara y no parezca oscuro.
- Se retiro la metadata `Sistema de informacion` de las tarjetas de proyecto.
- Se eliminaron los tres puntos inertes de las tarjetas de proyecto.

## Pendientes

- Conectar la metrica real de generaciones cuando se exponga un endpoint agregado.
- Agregar restauracion de proyectos archivados si se decide completar el flujo de ciclo de vida.
