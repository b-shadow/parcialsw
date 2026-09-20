# Rediseño de login y tema global claro/oscuro

## Que se implemento

- Se rediseño la pantalla de login con composicion dividida:
  - panel visual izquierdo usando `frontend/assets/login-izquierda.png`;
  - formulario derecho con identidad de marca, campos con iconos, recordar sesion y enlace de registro.
- Se agrego soporte global de modo claro y modo oscuro.
- Se creo un toggle reutilizable para cambiar tema.
- Se coloco el toggle en el topbar una vez iniciada sesion.
- Se agrego el toggle tambien en login para permitir cambiar tema antes de ingresar.
- Se actualizaron tokens de Tailwind para usar variables CSS de tema.
- Se agregaron overrides globales para que las pantallas existentes respondan al modo oscuro.

## Archivos creados o modificados

- `frontend/tailwind.config.js`
- `frontend/src/styles.css`
- `frontend/src/core/theme/themeStore.ts`
- `frontend/src/shared/components/ThemeToggle.tsx`
- `frontend/src/shared/layouts/AppLayout.tsx`
- `frontend/src/modules/gestion_acceso_usuarios/pages/LoginPage.tsx`
- `frontend/src/App.test.tsx`

## Decisiones tecnicas tomadas

- El tema se almacena en `localStorage` con la clave `case_theme`.
- El tema se aplica agregando o quitando la clase `dark` en `document.documentElement`.
- Los colores principales `ink`, `panel`, `accent` y `signal` pasan a depender de variables CSS.
- Se mantuvieron las clases existentes del sistema y se agregaron overrides CSS para evitar una refactorizacion masiva de todas las pantallas.
- El login importa el asset local mediante Vite para que quede incluido en el build.

## Cambios de arquitectura o base de datos

- No hubo cambios de base de datos.
- Se agrego un pequeno modulo frontend transversal para tema:
  - `core/theme/themeStore.ts`
  - `shared/components/ThemeToggle.tsx`

## Verificacion

- `npm run build`
- `npm test`

## Ajuste posterior de responsive y modo oscuro

- Se corrigio el posicionamiento del toggle en login para que no quede sobre la tarjeta en pantallas reducidas.
- Se reemplazo el posicionamiento absoluto del toggle por una fila propia dentro del layout del panel derecho.
- Se ajustaron los campos de correo y contrasena para que usen colores correctos segun el tema activo.
- Se agregaron estilos `dark:` explicitos en la tarjeta, labels, inputs, separadores y textos secundarios del login.
- Se reforzo el componente `ThemeToggle` con estilos propios para modo claro y oscuro.

## Correccion de estados hibridos del login

- Se elimino la dependencia de estilos `dark:` dentro de `LoginPage`.
- `LoginPage` ahora lee directamente el modo activo desde `useThemeStore`.
- Los colores del fondo, tarjeta, titulos, labels, campos, iconos, separadores y textos secundarios se calculan con `isDark`.
- Esto evita mezclas donde el fondo quedaba claro con tarjeta oscura o campos oscuros dentro del modo claro.

## Pendientes

- Revisar visualmente cada pantalla secundaria en modo oscuro para ajustes finos de contraste si se requiere pulido posterior.
- Evaluar code splitting del frontend si se desea eliminar la advertencia de bundle superior a 500 kB.
