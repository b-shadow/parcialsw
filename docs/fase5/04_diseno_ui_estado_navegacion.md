# Fase 5 - Diseno UI, estado y navegacion

## Sistema visual

Se mantiene Tailwind CSS como sistema principal de estilos.

Componentes compartidos:

- `Button`
- `Input`
- `Textarea`
- `Panel`
- `StatusBadge`

## Navegacion

La aplicacion usa `BrowserRouter` y rutas protegidas.

Rutas implementadas:

- `/login`
- `/registro`
- `/proyectos`
- `/proyectos/:projectId`
- `/proyectos/:projectId/uml/:diagramId`
- `/generacion`
- `/perfil`
- `/reportes`
- `/manual`

## Estado

Estado global:

- `useAuthStore`: token JWT y usuario autenticado.
- `useProjectStore`: proyecto activo.
- `useUmlStore`: clases, relaciones, validacion y seleccion del editor.

## Decisiones de interfaz

- Layout lateral para flujo operativo.
- Paneles compactos orientados a trabajo recurrente.
- Iconos Lucide en acciones principales.
- React Flow seleccionado para el canvas UML por su soporte de nodos, aristas, controles y personalizacion.
