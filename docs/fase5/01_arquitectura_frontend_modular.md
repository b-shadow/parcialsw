# Fase 5 - Arquitectura frontend modular

## Objetivo

Implementar el frontend principal de la plataforma CASE inteligente con React, TypeScript, Vite y Tailwind CSS, manteniendo separacion por dominios funcionales.

## Estructura aplicada

```text
frontend/src/
  core/
    api/
    auth/
    config/
    routes/
    websocket/
  modules/
    gestion_acceso_usuarios/
    gestion_proyectos_colaboracion/
    modelado_uml_inteligente/
    transformacion_generacion_software/
  shared/
    components/
    layouts/
    utils/
```

## Capas

- `core`: infraestructura transversal de API, JWT, rutas y WebSocket.
- `modules`: dominios funcionales definidos por el analisis del sistema.
- `shared`: componentes reutilizables, layout y utilidades.

## Decision tecnica

Se uso `react-router-dom` para rutas protegidas y navegacion interna. Se mantiene Zustand como estado ligero para autenticacion, proyecto activo y modelo UML. Axios concentra comunicacion REST y adjunta el token JWT mediante interceptor.
