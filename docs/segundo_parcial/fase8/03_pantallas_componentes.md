# Pantallas y componentes

## Pantallas

- `LoginPage`: correo, contrasena, validacion y estados de envio.
- `HomeShell`: topbar y navegacion inferior para proyectos, avisos y perfil.
- `ProjectsPage`: busqueda, refresco, metricas y apertura del proyecto.
- `ProjectDetailPage`: resumen, diagramas, actividad, versiones e IA.
- `DiagramViewerPage`: carga y visualizacion UML tactil.
- `NotificationsPage`: filtros y marcacion de lectura.
- `ProfilePage`: identidad, roles, cambio de contrasena y cierre de sesion.

## Reutilizacion

`CaseTopBar`, `EmptyState`, `ErrorPanel`, `StatusBadge`, `ProjectCard`, `NotificationTile` y los componentes UML se reutilizan. Los tamaños son estables, el texto aplica elipsis y las listas desplazan verticalmente para evitar overflow.

## Navegacion

La aplicacion usa `NavigationBar` inferior en el nivel principal y `Navigator` para proyecto/diagrama. El boton atras del sistema vuelve de diagrama a proyecto y de proyecto a inicio. El detalle usa una `TabBar` desplazable para que sus cinco vistas no se compriman.

## Criterio movil

No se replica el sidebar web. Las acciones frecuentes usan iconos conocidos y tooltips; los comandos destructivos o exclusivos de escritorio no aparecen.
