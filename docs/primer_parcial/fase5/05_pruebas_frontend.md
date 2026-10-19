# Fase 5 - Pruebas frontend

## Herramientas

- ESLint para calidad estatica.
- TypeScript para verificacion de tipos.
- Vitest para pruebas unitarias.
- Testing Library para render de componentes React.
- Vite build para validacion de empaquetado.

## Prueba implementada

Archivo:

- `frontend/src/App.test.tsx`

Cobertura:

- Render inicial de la aplicacion.
- Redireccion a inicio de sesion cuando no existe token.
- Integracion basica de rutas protegidas.

## Validacion ejecutada

```powershell
npm run lint
npm run test
npm run build
```

Resultado:

- Lint correcto.
- 1 prueba correcta.
- Build de produccion correcto.
