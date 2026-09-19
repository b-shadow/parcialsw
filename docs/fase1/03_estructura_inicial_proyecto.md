# Fase 1 - Estructura inicial del proyecto

## Estructura creada

```text
.
|-- frontend/
|   |-- src/
|   |   |-- core/
|   |   |-- modules/
|   |   |-- shared/
|   |   |-- App.tsx
|   |   `-- main.tsx
|   |-- package.json
|   |-- vite.config.ts
|   |-- tailwind.config.js
|   `-- README.md
|-- backend/
|   |-- app/
|   |   |-- core/
|   |   |-- modules/
|   |   |-- websocket/
|   |   `-- main.py
|   |-- migrations/
|   |-- pyproject.toml
|   `-- README.md
|-- ai-engine/
|   |-- ai_engine/
|   |-- datasets/
|   |-- inference/
|   |-- models/
|   |-- preprocessing/
|   |-- prompts/
|   |-- services/
|   |-- training/
|   |-- validators/
|   |-- pyproject.toml
|   `-- README.md
|-- docs/
|   `-- fase1/
|-- docker-compose.yml
|-- .gitignore
`-- README.md
```

## Criterio aplicado

La estructura separa productos principales sin romper la arquitectura por dominios. Backend y frontend contienen los cuatro paquetes funcionales definidos por la documentacion original.

