# Ajuste de navegacion: gestion de proyectos y modo colaborativo

## Que se implemento

- Se separo la navegacion entre gestion administrativa del proyecto y modo colaborativo.
- La ruta `/proyectos` muestra el listado general y permite entrar a gestion o al modo colaborativo.
- La ruta `/proyectos/{projectId}` queda dedicada a gestion del proyecto.
- La ruta `/proyectos/{projectId}/colaborativo` queda dedicada a diagramas, IA, XMI y versionado.
- Se agrego una pantalla para editar datos del proyecto y administrar colaboradores.
- Se agrego soporte backend para cambiar rol de colaboradores y quitarlos del proyecto.

## Archivos creados o modificados

- `backend/app/modules/proyectos_colaboracion/schemas/project.py`
- `backend/app/modules/proyectos_colaboracion/repositories/member_repository.py`
- `backend/app/modules/proyectos_colaboracion/services/project_service.py`
- `backend/app/modules/proyectos_colaboracion/routers/projects.py`
- `frontend/src/core/routes/routes.tsx`
- `frontend/src/modules/gestion_acceso_usuarios/services/userService.ts`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectsPage.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectManagementPage.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/pages/ProjectWorkspacePage.tsx`
- `frontend/src/modules/gestion_proyectos_colaboracion/services/projectService.ts`

## Decisiones tecnicas tomadas

- Se mantuvo `ProjectWorkspacePage` como modo colaborativo para no mezclar administracion de colaboradores con modelado UML.
- La administracion de colaboradores usa usuarios registrados existentes y permite seleccionar rol `EDITOR` u `ORGANIZADOR`.
- El propietario del proyecto no puede perder el rol `ORGANIZADOR` ni ser quitado del proyecto.
- No se permite dejar un proyecto sin al menos un organizador.

## Cambios de arquitectura o base de datos

- No se agregaron migraciones ni tablas.
- Se ampliaron contratos REST:
  - `PATCH /api/v1/projects/{project_id}/members/{member_id}`
  - `DELETE /api/v1/projects/{project_id}/members/{member_id}`

## Verificacion

- `npm run build`
- `python -m pytest tests/test_phase4_contracts.py`
- Prueba funcional por API:
  - crear usuario colaborador,
  - crear proyecto,
  - agregar colaborador,
  - cambiar rol,
  - quitar colaborador.

## Pendientes

- Agregar busqueda de usuarios por correo en backend si el volumen de usuarios crece.
- Incorporar una vista detallada de permisos por colaborador si se requiere administrar permisos finos desde UI.
