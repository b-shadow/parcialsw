# Frontend web

Aplicacion React + TypeScript + Vite + Tailwind CSS para la plataforma CASE inteligente.

La estructura inicial queda organizada por los cuatro paquetes funcionales:

- `gestion_acceso_usuarios`
- `gestion_proyectos_colaboracion`
- `modelado_uml_inteligente`
- `transformacion_generacion_software`

## Fase 5

La fase implementa:

- Rutas protegidas.
- Cliente HTTP Axios con JWT.
- Estado global con Zustand.
- WebSocket colaborativo por proyecto.
- Editor UML inicial con React Flow.
- Interfaces de transformacion, Spring Boot y Flutter.

## Ejecucion

```powershell
npm install
npm run dev
npm run lint
npm run test
npm run build
```

## Variables

- `VITE_API_BASE_URL`: por defecto `http://127.0.0.1:8000/api/v1`.
- `VITE_WS_BASE_URL`: por defecto `ws://127.0.0.1:8000`.
