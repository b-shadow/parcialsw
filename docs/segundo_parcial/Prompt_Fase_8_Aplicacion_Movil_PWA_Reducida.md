# PROMPT FASE 8: APLICACION MOVIL FLUTTER REDUCIDA

> **Decision arquitectonica vigente (17 de octubre de 2026):** la Fase 8 se implementa como una aplicacion Flutter independiente dentro de `mobile/`, con destinos Android e iOS. Esta decision sustituye las instrucciones historicas de este documento que indicaban fortalecer React como PWA o prohibian crear un cliente Flutter. Los requisitos funcionales de consulta, solo lectura, permisos, IA, notificaciones, WebSocket, offline honesto y pruebas se conservan y se traducen a capacidades nativas Flutter. La implementacion y criterios finales se documentan en `docs/segundo_parcial/fase8/`.

## 0. Instruccion maestra

Implementar la Fase 8 de la segunda parte de CASE Inteligente como una aplicacion Flutter en `mobile/`, reducida, informativa, segura y coherente con la plataforma web.

La aplicacion Flutter es un cliente de la plataforma existente, no una copia del editor ni parte del generador Flutter. Debe usar los mismos contratos de backend, autenticacion, permisos, WebSocket, conversaciones, versiones y notificaciones desarrollados en las Fases 1 a 7.

El objetivo movil es permitir que una persona pueda:

- Iniciar sesion.
- Consultar sus proyectos.
- Consultar miembros y actividad reciente.
- Ver diagramas UML sin editarlos manualmente.
- Recorrer diagramas grandes mediante gestos tactiles.
- Consultar versiones cuando su rol lo permita.
- Conversar con la IA unica del proyecto.
- Consultar el estado de generaciones.
- Recibir y abrir notificaciones.
- Instalar la PWA en un dispositivo compatible.
- Consultar informacion previamente sincronizada cuando la red no este disponible.

No trasladar al movil herramientas complejas que requieran precision de escritorio. No ofrecer controles que parezcan editar si solo son decorativos. No prometer funcionamiento offline para operaciones que necesitan al backend, Ollama/Qwen, PostgreSQL o WebSocket.

Antes de editar, inspeccionar la implementacion real de:

- `vite.config.ts`.
- `vite-plugin-pwa`.
- `main.tsx`.
- manifiesto y service worker.
- `AppLayout`.
- rutas protegidas.
- autenticacion.
- `JointUmlCanvas`.
- proyectos y workspace colaborativo.
- asistente inteligente.
- historial/versiones.
- bandeja y Web Push de Fase 7.
- WebSocket y reconexion.

La implementacion debe conservar la experiencia completa de escritorio. Un cambio movil no puede degradar la edicion UML, generacion, administracion o editor de estilos en pantallas grandes.

---

## 1. Resultado funcional buscado

Al finalizar esta fase:

1. CASE Inteligente se puede instalar como PWA en navegadores compatibles.
2. El manifiesto tiene nombre, iconos, colores, alcance y modo de pantalla correctos.
3. La aplicacion abre desde el icono instalado sin mostrar una pagina en blanco.
4. Las rutas internas funcionan al recargar desde hosting estatico como Vercel.
5. Existe una composicion movil clara con cabecera compacta y navegacion inferior.
6. La composicion de escritorio permanece sin regresiones.
7. El usuario inicia sesion y conserva el mismo modelo de permisos.
8. La lista de proyectos se puede explorar con una mano y sin desbordamiento horizontal.
9. El detalle del proyecto resume estado, miembros, diagramas, actividad y generaciones.
10. El visor UML es estrictamente de solo lectura en modo movil reducido.
11. El visor soporta pan, pinch-to-zoom, zoom por botones, centrar y ajustar a contenido.
12. Tocar una clase abre una ficha de lectura con atributos y metodos.
13. Tocar una relacion muestra tipo, extremos y multiplicidades.
14. Diagramas grandes se recorren sin mover elementos ni bloquear toda la pagina.
15. El usuario consulta la actividad persistente de la Fase 7.
16. El propietario u organizador puede consultar versiones, pero no restaurarlas desde la experiencia movil reducida.
17. La conversacion con la IA mantiene memoria compartida y secuencia del proyecto.
18. La IA reconoce que la superficie actual es movil de consulta.
19. Las propuestas estructurales pueden leerse, pero su aplicacion se deriva al escritorio.
20. Se consultan generaciones en curso, completadas o fallidas.
21. No se inician operaciones pesadas de generacion desde la superficie movil.
22. La bandeja muestra notificaciones persistentes y contador no leido.
23. Un push abre exactamente el proyecto, diagrama, conversacion o generacion relacionado.
24. La aplicacion reacciona correctamente al volver del fondo.
25. El WebSocket se reconecta sin duplicar eventos.
26. La PWA muestra un estado offline honesto.
27. El shell y datos de lectura previamente sincronizados pueden mostrarse offline.
28. Las mutaciones no se inventan, no se encolan silenciosamente y no se marcan como exitosas offline.
29. Cambiar de usuario o cerrar sesion elimina la cache privada correspondiente.
30. Las pruebas cubren Android, iOS PWA cuando sea posible, pantallas pequenas, accesibilidad, offline y reconexion.

---

## 2. Alineacion obligatoria entre fases

### 2.1. Fase 1: contratos y persistencia

Consumir los contratos versionados ya definidos. No crear DTO moviles incompatibles con los modelos web. Si se requiere un endpoint de resumen, debe componer los mismos servicios y devolver referencias estables.

### 2.2. Fase 2: motor unico de IA

La PWA usa el mismo orquestador Ollama/Qwen y el mismo fallback. No existe una personalidad movil diferente. Solo se agrega contexto de superficie para que el orquestador sepa que el cliente no puede ejecutar herramientas complejas.

### 2.3. Fase 3: conversacion colaborativa

La conversacion movil:

- usa la misma conversacion por proyecto;
- respeta secuencia e idempotencia;
- muestra mensajes enviados desde escritorio;
- recibe nuevos mensajes por WebSocket;
- no crea un historial local paralelo;
- conserva confirmaciones pendientes;
- no aplica acciones estructurales ocultas.

### 2.4. Fase 4: especificacion funcional de metodos

La ficha de clase y metodo debe poder mostrar firmas y descripciones funcionales existentes en modo lectura. No se editan especificaciones complejas desde movil.

### 2.5. Fase 5: generacion coordinada

Mostrar ejecuciones, componentes, estado, diagnosticos resumidos y disponibilidad de artefactos. No iniciar Spring Boot/Flutter ni descargar archivos enormes automaticamente en datos moviles.

### 2.6. Fase 6: tema y previsualizacion

El editor visual completo permanece en escritorio. En movil se puede consultar una miniatura o resumen del tema/previsualizacion si ya existe un contrato liviano, pero no duplicar el editor de estilos.

### 2.7. Fase 7: versiones, bitacora y notificaciones

Reutilizar:

- actividad paginada;
- versiones resumidas;
- bandeja persistente;
- contador no leido;
- deep links estructurados;
- Web Push;
- eventos de invalidacion;
- preferencias.

La restauracion sigue restringida a escritorio aunque el usuario tenga rol organizador. El backend mantiene permisos; la PWA simplemente no ofrece esa operacion.

### 2.8. Entrega a Fase 9

Dejar pruebas y evidencia para validacion integral responsive, PWA, offline, accesibilidad, permisos, WebSocket, push, consumo de red y regresion de escritorio.

---

## 3. Alcance incluido

### 3.1. Autenticacion

- Login responsive.
- Recuperacion clara de sesion existente.
- Cierre de sesion.
- Estado de sesion expirada.
- Mensaje de backend inaccesible.
- Redireccion al destino solicitado despues de autenticar.

### 3.2. Proyectos

- Lista de proyectos.
- Busqueda local sobre resultados cargados.
- Filtro por estado.
- Resumen de rol.
- Detalle del proyecto.
- Miembros.
- Actividad reciente.
- Diagramas.
- Estado de generaciones.

### 3.3. UML

- Lista de diagramas.
- Visor de solo lectura.
- Pan y zoom tactil.
- Ajustar al contenido.
- Restablecer vista.
- Ficha de clase.
- Ficha de relacion.
- Leyenda de notacion.

### 3.4. IA

- Ver conversacion compartida.
- Enviar consultas de texto.
- Dictado mediante capacidades del navegador si ya esta soportado y hay permiso.
- Ver propuestas y diagnosticos.
- Recibir respuesta asincrona.
- Indicar cuando una accion requiere abrir escritorio.

### 3.5. Historial y versiones

- Actividad reciente para miembros.
- Versiones para propietario/organizador.
- Metadatos y contenido resumido.
- Sin boton de restauracion.

### 3.6. Generaciones

- Lista de ejecuciones.
- Estado y progreso.
- Componentes generados.
- Errores resumidos.
- Acceso a detalle.
- Descarga solo mediante accion explicita y advertencia de tamano.

### 3.7. Notificaciones

- Bandeja.
- No leidas.
- Marcar como leida.
- Deep link.
- Preferencias basicas.
- Habilitar/deshabilitar Web Push.

---

## 4. Alcance excluido

No incluir inicialmente:

- Crear, mover, redimensionar o renombrar clases en el lienzo movil.
- Crear relaciones con gestos.
- Editar atributos y metodos desde el diagrama.
- Importar imagen o XMI desde movil.
- Exportar diagramas complejos desde movil.
- Restaurar versiones.
- Guardar versiones manuales.
- Editar tema Flutter.
- Previsualizacion completa interactiva del frontend generado.
- Iniciar generacion Spring Boot/Flutter.
- Configurar URLs de backend generado.
- Administracion global de usuarios.
- Bitacora administrativa global.
- Cambios avanzados de roles/permisos.
- Resolucion visual de conflictos.
- Ejecucion local de Ollama en el telefono.
- Emulacion de backend dentro del service worker.

Una ruta directa hacia una herramienta excluida debe mostrar una explicacion corta y ofrecer `Abrir en escritorio`, no renderizar controles rotos.

---

## 5. Principios de producto

### 5.1. Una sola aplicacion

No crear `mobile-app/`, un segundo repositorio ni endpoints duplicados. La PWA es una presentacion responsive del frontend actual.

### 5.2. Lectura primero

En movil se prioriza consultar, comprender y recibir novedades. Las acciones disponibles deben ser pequenas, seguras y adecuadas para tactil.

### 5.3. Permisos iguales

El dispositivo no cambia permisos. Un visualizador sigue sin editar; un organizador sigue autorizado en backend, aunque ciertas herramientas se oculten por limitacion de superficie.

### 5.4. Offline honesto

Offline significa shell instalable y lectura de datos previamente sincronizados. No significa que PostgreSQL, FastAPI, Ollama o WebSocket funcionen dentro del navegador.

### 5.5. Mismo recurso, misma URL

Un proyecto o diagrama debe tener una URL canonica. La composicion cambia por capacidad de pantalla, no mediante URLs incompatibles.

### 5.6. Progresividad

Si una capacidad no existe, la aplicacion degrada con claridad:

- sin Push: bandeja interna sigue funcionando;
- sin instalacion: web responsive sigue funcionando;
- sin WebSocket: polling/revalidacion acotada;
- sin red: cache de lectura;
- sin dictado: entrada de texto;
- sin IndexedDB: shell y mensaje offline.

---

## 6. Arquitectura elegida

Usar:

- React 19 existente.
- React Router existente.
- Vite existente.
- `vite-plugin-pwa` ya instalado.
- Workbox generado por el plugin.
- Tailwind/CSS existente.
- Zustand existente para estado efimero/global actual.
- Axios existente para API.
- JointJS existente para render UML.
- WebSocket existente.
- Web Push existente.
- IndexedDB para cache de lectura privada.

Para IndexedDB, usar una envoltura pequena y probada como `idb` si se aprueba una dependencia adicional. Si no se agrega, encapsular la API nativa en un modulo probado; no dispersar llamadas a IndexedDB por componentes.

No agregar un framework movil completo. No envolver en Capacitor durante esta fase. No introducir Redux si Zustand ya resuelve el estado actual.

---

## 7. Deteccion de experiencia movil

No usar el user agent como regla principal.

Crear un hook central, por ejemplo:

```ts
type AppSurface = "mobile" | "tablet" | "desktop";

useAppSurface(): {
  surface: AppSurface;
  isTouchPrimary: boolean;
  isStandalone: boolean;
  isOnline: boolean;
}
```

Basarse en:

- media queries de ancho;
- `pointer: coarse` como informacion complementaria;
- `display-mode: standalone`;
- eventos `online/offline`;
- `visualViewport` cuando sea necesario para teclado.

Breakpoints recomendados, alineados con Tailwind:

- movil: menor de `768px`;
- tablet: `768px` a menor de `1024px`;
- escritorio: `1024px` o mayor.

La restriccion de herramientas se aplica a la superficie reducida y no a una marca de telefono. Un navegador de escritorio muy angosto debe recibir una interfaz util, no quedar inutilizable.

---

## 8. Rutas y navegacion canonica

Conservar rutas existentes siempre que sea posible:

```text
/login
/proyectos
/proyectos/:projectId
/proyectos/:projectId/colaborativo
/proyectos/:projectId/uml/:diagramId
/generacion
/perfil
```

Agregar query params o estado para paneles:

```text
?tab=activity
?tab=diagrams
?panel=notifications
?conversation=project
?generation_id=uuid
```

No crear `/mobile/...` para cada pantalla. Eso duplicaria deep links y estado.

### 8.1. Guard de superficie

Cuando una ruta contiene una herramienta excluida:

- mostrar vista de lectura equivalente;
- ocultar toolbar de edicion;
- impedir handlers de mutacion;
- ofrecer abrir en una pantalla mayor;
- nunca confiar solo en CSS `display:none`.

### 8.2. Recarga directa

Configurar hosting para devolver `index.html` en rutas SPA. Incluir `vercel.json` o mecanismo equivalente ya usado, sin romper endpoints del backend.

---

## 9. Layout movil

Crear una composicion especifica dentro de `AppLayout`, reutilizando identidad visual.

### 9.1. Cabecera

- Altura compacta estable.
- Nombre de pantalla o proyecto.
- Indicador offline discreto.
- Boton de notificaciones con badge.
- Menu secundario para perfil, tema, push y cierre de sesion.
- Respetar `env(safe-area-inset-top)`.

### 9.2. Navegacion inferior

Maximo cinco destinos:

1. Proyectos.
2. Actividad/contexto del proyecto cuando exista.
3. Diagramas.
4. IA.
5. Perfil o Mas.

Los destinos dependientes de proyecto quedan deshabilitados o vuelven a proyectos cuando no hay contexto.

Usar iconos Lucide, etiquetas cortas y area tactil minima de 44x44 CSS px.

### 9.3. Contenido

- Padding horizontal de 16px en movil.
- Ancho completo, sin tarjetas dentro de tarjetas.
- Espacio inferior suficiente para navegacion y safe area.
- No usar tablas horizontales para informacion principal.
- Convertir tablas a listas de filas etiquetadas.
- Titulos proporcionados al contexto.

### 9.4. Capas flotantes

Asistente, historial y notificaciones no pueden superponerse.

En movil:

- una sola sheet/modal abierta a la vez;
- coordinacion mediante un store de overlays;
- fondo y foco controlados;
- boton del asistente por encima de la barra inferior sin tapar acciones;
- cerrar al navegar.

---

## 10. Conservacion del escritorio

Mantener el sidebar, topbar y herramientas actuales para `lg` o superficie de escritorio.

No reemplazar toda la aplicacion por una unica estructura movil. Separar componentes de shell:

```text
AppLayout
  DesktopShell
  MobileShell
  RouteOutlet
```

El `Outlet` no debe desmontarse innecesariamente al cambiar orientacion, porque podria perder estado en formularios de escritorio. Si el cambio de shell exige remontaje, guardar estado seguro o bloquear transicion durante una mutacion.

Crear pruebas visuales para ambos modos.

---

## 11. PWA: manifiesto

Completar la configuracion de `VitePWA`.

Campos minimos:

```ts
manifest: {
  id: "/",
  name: "CASE Inteligente",
  short_name: "CASE",
  description: "Consulta proyectos, diagramas y actividad de CASE Inteligente.",
  lang: "es",
  dir: "ltr",
  start_url: "/proyectos?source=pwa",
  scope: "/",
  display: "standalone",
  orientation: "any",
  theme_color: "#0f766e",
  background_color: "#f8fafc",
  categories: ["productivity", "developer", "education"]
}
```

Agregar iconos raster reales:

- 192x192 `any`.
- 512x512 `any`.
- 192x192 `maskable`.
- 512x512 `maskable`.
- `apple-touch-icon` 180x180.
- favicon apropiado.

No depender unicamente de SVG con `sizes: any`, porque el soporte de instalacion y maskable varia.

Validar que el contenido importante quede dentro de la zona segura maskable.

### 11.1. Shortcuts opcionales

Agregar accesos a:

- Proyectos.
- Notificaciones.

No agregar shortcuts a recursos que requieren un `projectId` desconocido.

---

## 12. PWA: registro y actualizaciones

Cambiar `registerType: "autoUpdate"` a una estrategia controlada si la actualizacion inmediata puede interrumpir una conversacion o formulario.

Preferir:

```ts
registerType: "prompt"
```

Crear un componente de actualizacion que:

- informe que existe una version nueva;
- permita actualizar ahora;
- posponga mientras hay una mutacion activa;
- recargue una vez activado el nuevo worker;
- no forme bucles de recarga;
- pueda descartarse temporalmente.

En primer arranque, mostrar disponibilidad offline solo despues de que el service worker controle la pagina y los assets esenciales esten almacenados.

---

## 13. Estrategia de cache del service worker

Separar recursos publicos, shell y datos autenticados.

### 13.1. Precache

Incluir:

- HTML base.
- JS y CSS con hash.
- fuentes locales.
- iconos.
- pagina/fallback offline.
- assets esenciales.

No precachear sourcemaps de produccion ni archivos de desarrollo.

### 13.2. Navegaciones

Usar `NetworkFirst` con timeout corto y fallback al shell precacheado. Una ruta React debe cargar offline si la aplicacion se abrio al menos una vez.

### 13.3. Assets estaticos

Usar `CacheFirst` para assets con hash y expiracion razonable para imagenes no versionadas.

### 13.4. API autenticada

Mantener peticiones API como `NetworkOnly` en Workbox. No almacenar respuestas privadas en Cache Storage compartida porque la cache key HTTP no separa de forma segura por token/usuario.

La lectura offline se implementa en la capa de aplicacion mediante IndexedDB, con usuario, contrato y fecha explicitos.

### 13.5. Mutaciones

Nunca cachear ni encolar automaticamente:

- POST de login.
- mensajes de IA.
- confirmaciones.
- cambios UML.
- cambios de tema.
- versiones.
- restauraciones.
- generaciones.
- cambios de membresia.

Background Sync queda fuera para mutaciones durante esta fase, salvo una cola futura disenada con idempotencia y confirmacion visible.

---

## 14. Pagina y estado offline

Crear un estado offline integrado, no una pantalla de error generica.

Mostrar:

- indicador `Sin conexion`;
- fecha de ultima sincronizacion;
- datos disponibles en cache;
- acciones que requieren conexion;
- boton `Reintentar`;
- explicacion cuando un recurso nunca fue sincronizado.

No mostrar:

- spinners infinitos;
- errores CORS como si fueran offline;
- datos viejos sin fecha;
- botones mutables aparentemente activos;
- mensajes de exito falsos.

La pagina offline independiente se usa solo si el shell principal no puede arrancar.

---

## 15. Cache privada con IndexedDB

Crear una capa unica, por ejemplo:

```text
frontend/src/core/offline/
  offlineDatabase.ts
  offlineRepository.ts
  offlinePolicy.ts
  offlineSync.ts
```

Stores sugeridos:

- `project_summaries`.
- `project_details`.
- `project_members`.
- `project_activity`.
- `diagram_summaries`.
- `diagram_snapshots`.
- `version_summaries`.
- `generation_summaries`.
- `notification_summaries`.
- `sync_metadata`.

Cada registro privado incluye:

- `user_id` o namespace derivado.
- `resource_id`.
- `schema_version`.
- `project_revision` cuando aplique.
- `cached_at` UTC.
- `expires_at`.
- contenido validado.

### 15.1. Politica de escritura

Solo guardar respuestas GET exitosas y autorizadas. Validar forma antes de persistir. Una respuesta parcial o error no reemplaza una copia buena.

### 15.2. Politica de lectura

1. Intentar red cuando existe conectividad.
2. Presentar cache inmediatamente si mejora UX, marcada como sincronizada en una fecha.
3. Revalidar.
4. Reemplazar solo con respuesta valida.
5. Si red falla, conservar cache y explicar.

### 15.3. Purga

Eliminar cache privada:

- al cerrar sesion;
- al cambiar de cuenta;
- al recibir remocion de proyecto;
- cuando expira segun politica;
- mediante accion `Borrar datos sin conexion`.

No cachear contrasenas, access tokens, refresh tokens, claves push ni secretos.

---

## 16. Limites de funcionamiento offline

Documentar y reflejar en UI:

| Funcion | Offline |
| --- | --- |
| Abrir shell PWA | Si, despues de primera carga |
| Ver proyectos sincronizados | Si, lectura |
| Ver detalle sincronizado | Si, lectura |
| Ver UML sincronizado | Si, lectura |
| Ver actividad sincronizada | Si, historico cacheado |
| Ver notificaciones sincronizadas | Si, historico cacheado |
| Login nuevo | No |
| Renovar sesion | No |
| Enviar mensaje a IA | No |
| Recibir respuesta nueva | No |
| WebSocket | No |
| Generar software | No |
| Restaurar version | No y ademas excluido en movil |
| Recibir Web Push nuevo | Requiere conectividad del dispositivo |

Si frontend y backend estan en la misma red local pero no existe Internet, las operaciones online pueden funcionar siempre que el dispositivo pueda alcanzar el backend y la PWA ya este instalada/cargada. `navigator.onLine` no basta para decidir; una solicitud real determina disponibilidad del backend.

---

## 17. Topologias y URLs

### 17.1. Produccion recomendada

```text
PWA HTTPS publica
  -> API HTTPS publica
  -> WSS publico
```

### 17.2. Desarrollo en la misma PC

```text
http://localhost:5173
  -> http://127.0.0.1:8081/api/v1
  -> ws://127.0.0.1:8081
```

La excepcion de secure context para `localhost` aplica al mismo equipo, no al telefono.

### 17.3. Telefono en red local

Desde el telefono, `127.0.0.1` apunta al telefono, no a la PC. Usar un hostname/IP LAN alcanzable y configurar CORS/origen y firewall. Para instalacion PWA y muchas APIs del navegador se necesita HTTPS, salvo excepciones de desarrollo limitadas.

### 17.4. Frontend Vercel con backend HTTP local

No prometer compatibilidad universal. Un sitio HTTPS que llama HTTP puede ser bloqueado por contenido mixto, CORS o Private Network Access. La opcion fiable es exponer backend por HTTPS o servir frontend y backend mediante un origen/reverse proxy compatible.

El prompt de implementacion debe documentar estas diferencias sin insertar IPs fijas en el codigo.

---

## 18. Configuracion de entorno

Mantener variables:

```dotenv
VITE_API_BASE_URL=https://api.example.com/api/v1
VITE_WS_BASE_URL=wss://api.example.com
VITE_APP_ENV=production
VITE_PWA_OFFLINE_CACHE_ENABLED=true
VITE_PWA_CACHE_MAX_AGE_HOURS=72
```

Reglas:

- API y WS deben derivarse de configuracion, no hardcodearse.
- En produccion HTTPS, WS debe usar WSS.
- Validar variables al arrancar y mostrar diagnostico seguro.
- No incluir secretos en variables `VITE_*`.
- No usar valores de ejemplo en build productivo silenciosamente.

---

## 19. Autenticacion movil

Reutilizar el contrato actual de login y usuario.

### 19.1. Arranque

Estados explicitos:

```text
booting
authenticated-online
authenticated-cached
anonymous
session-expired
backend-unreachable
```

No redirigir al login solo porque `/me` fallo por red. Si existe una sesion local y datos cacheados, permitir modo lectura offline con advertencia. Si el backend responde 401/403, invalidar sesion segun contrato.

### 19.2. Credenciales

No almacenar credenciales en IndexedDB ni service worker. No copiar token a caches. Si se mantiene el token existente en localStorage por compatibilidad, no ampliar su exposicion y registrar como riesgo a endurecer. Una migracion a cookie HttpOnly debe hacerse de extremo a extremo, no parcialmente en esta fase.

### 19.3. Cierre de sesion

- Limpiar store de usuario.
- Limpiar cache privada del usuario.
- Cerrar WebSockets.
- Ocultar notificaciones locales.
- Decidir de forma explicita si se conserva o elimina la suscripcion push del dispositivo.
- Volver a login.

---

## 20. Lista movil de proyectos

Recomponer la lista existente para movil.

Cada fila muestra:

- Nombre.
- Estado.
- Rol del usuario.
- Fecha de ultima actividad.
- Numero de diagramas si el contrato lo ofrece.
- Indicador de novedades.
- Accion primaria `Abrir` mediante toda la fila o boton claro.

No mostrar tres grandes botones de escritorio por proyecto. Acciones secundarias van en menu cuando esten permitidas. Archivar y crear proyecto pueden quedar fuera de la superficie reducida si no estan en alcance.

### 20.1. Estados

- Skeleton de altura estable.
- Error con reintento.
- Vacio.
- Offline con datos.
- Offline sin datos.
- Proyecto archivado.

### 20.2. Rendimiento

- Paginacion/cursor si la API lo soporta.
- Evitar cargar diagramas completos para cada fila.
- No descargar actividad de todos los proyectos al inicio.
- Mantener busqueda debounced cuando consulte servidor.

---

## 21. Detalle movil del proyecto

Organizar en tabs o segmentos compactos:

```text
Resumen | Diagramas | Actividad | IA | Mas
```

`Resumen`:

- nombre y descripcion;
- estado;
- rol;
- ultima actividad;
- miembros resumidos;
- generacion mas reciente;
- accesos a diagramas.

`Diagramas`:

- lista, tipo, estado y fecha;
- abrir visor;
- sin controles de crear/eliminar/importar.

`Actividad`:

- feed de Fase 7;
- agrupacion y carga incremental.

`IA`:

- conversacion del proyecto.

`Mas`:

- miembros;
- versiones si tiene permiso;
- generaciones;
- configuracion de notificaciones del proyecto.

---

## 22. Miembros y permisos

Mostrar:

- nombre;
- correo si la politica lo permite;
- rol;
- estado/invitacion cuando corresponda;
- indicador del usuario actual.

No ofrecer gestion avanzada. Si el usuario movil tiene permiso, informar que la administracion de colaboradores esta disponible en escritorio.

Las respuestas del backend deben respetar minimizacion de datos. No cachear correos mas tiempo del necesario.

---

## 23. Visor UML de solo lectura

No reutilizar el editor completo dejando botones ocultos. Extraer un modo real:

```ts
type JointUmlCanvasMode = "edit" | "readonly";
```

En `readonly`:

- no hay drag de clases;
- no hay rename por doble clic;
- no hay creacion de relaciones;
- no hay handles/anchors de edicion;
- no hay persistencia de posiciones;
- seleccionar solo abre detalles;
- pan y zoom siguen habilitados;
- teclado no ejecuta Delete ni comandos de edicion;
- WebSocket solo invalida/actualiza lectura.

Hacer callbacks de mutacion opcionales o separar `UmlDiagramRenderer` de `UmlDiagramEditor`. No pasar funciones vacias como unica proteccion.

---

## 24. Gestos del visor

### 24.1. Pan

- Un dedo arrastra el viewport sobre el lienzo.
- El gesto inicia solo dentro del visor.
- Evitar mover elementos.
- Permitir scroll de la pagina en zonas exteriores.
- Definir `touch-action` con cuidado.

### 24.2. Pinch-to-zoom

- Dos puntos tactiles calculan distancia inicial.
- Zoom centrado en el punto medio del gesto.
- Limitar escala entre valores seguros.
- No saltar al levantar un dedo.
- No disparar seleccion accidental.

### 24.3. Doble toque

Usarlo solo si no interfiere con accesibilidad. Preferir boton `Ajustar` como accion predecible.

### 24.4. Botones

Controles estables:

- acercar;
- alejar;
- ajustar;
- restablecer;
- abrir leyenda.

Cada boton tiene icono, label accesible, tooltip donde aplique y 44x44 px.

### 24.5. Limites

- Evitar zoom infinito.
- Evitar perder el diagrama completamente fuera de pantalla.
- Permitir margen alrededor del contenido.
- Persistir viewport por diagrama solo durante sesion, no como posicion UML.

---

## 25. Ajustar a contenido

Calcular bounds reales de:

- clases;
- association classes;
- etiquetas de relaciones cuando sea posible;
- vertices/rutas.

Algoritmo:

1. Obtener bounding box de celdas renderizadas.
2. Agregar padding.
3. Calcular escala para ancho y alto del contenedor.
4. Aplicar `min(max(scale, MIN_ZOOM), MAX_ZOOM)`.
5. Centrar.
6. Recalcular en orientacion/cambio de tamano mediante `ResizeObserver`.

No usar exclusivamente dimensiones fijas `4200x3000` para decidir encuadre.

---

## 26. Ficha de clase y relacion

Tocar una clase abre un bottom sheet de lectura.

Clase:

- nombre y estereotipo;
- descripcion;
- atributos con visibilidad, tipo y restricciones;
- metodos con parametros y retorno;
- resumen funcional cuando exista;
- relaciones conectadas.

Relacion:

- tipo;
- origen y destino;
- multiplicidades;
- navegabilidad;
- etiqueta;
- association class relacionada.

No permitir editar desde la ficha. Ofrecer `Ver en escritorio` cuando el usuario necesite cambiarla.

---

## 27. Diagramas grandes y rendimiento

Medir con diagramas de referencia:

- 20 clases.
- 50 clases.
- 100 clases con relaciones.
- textos largos.
- varias association classes.

Controles:

- Lazy-load de JointJS solo al abrir visor.
- Memoizar transformacion de modelo a celdas.
- No reconstruir todo el grafo por cada evento no relacionado.
- Agrupar actualizaciones WebSocket.
- Evitar sombras/filtros costosos en cientos de nodos.
- Mostrar progreso al cargar modelos grandes.
- Mantener interaccion fluida en dispositivo de gama media.

Si se supera un limite soportado, informar y permitir ver lista de clases; no bloquear ni cerrar la aplicacion.

---

## 28. Sincronizacion del visor

Al abrir online:

1. Mostrar snapshot cacheado si existe.
2. Solicitar revision actual.
3. Reemplazar con respuesta valida.
4. Guardar snapshot actualizado.
5. Conectar WebSocket del proyecto.

Ante evento UML:

- aplicar actualizacion incremental si el contrato es completo y secuencial;
- de lo contrario invalidar y recargar;
- deduplicar por `event_id/client_event_id`;
- actualizar `last_sequence`.

Ante `PROJECT_STATE_INVALIDATED` por restauracion:

- descartar snapshot en memoria;
- conservar cache anterior solo hasta recibir nuevo estado;
- recargar modelo completo;
- escribir nueva revision en IndexedDB;
- mostrar aviso.

---

## 29. Conversacion IA movil

Reutilizar la conversacion de Fase 3 mediante una vista adaptada.

### 29.1. Capacidades

- Scroll virtual o paginacion inversa.
- Mensajes con estado.
- Respuestas parciales si el backend transmite.
- Reintento idempotente.
- Dictado opcional.
- Indicador de conexion.
- Abrir referencias a clases/diagramas.
- Ver propuesta estructurada.

### 29.2. Contexto de superficie

Enviar metadata no autoritativa:

```json
{
  "client_context": {
    "surface": "mobile_readonly",
    "supports_structural_confirmation": false,
    "active_project_id": "uuid",
    "active_diagram_id": "uuid"
  }
}
```

El backend no confia en ese bloque para permisos, pero lo usa para adaptar respuesta.

### 29.3. Solicitudes de edicion

Si el usuario pide `conecta Cliente con Pedido` desde la PWA reducida:

- la IA entiende la intencion;
- puede explicar y preparar una propuesta;
- no aplica silenciosamente;
- devuelve estado `desktop_confirmation_required`;
- conserva la propuesta en la conversacion;
- muestra accion `Continuar en escritorio`.

No responder como si la IA fuera incapaz. La limitacion es la superficie de confirmacion, no el motor.

### 29.4. Offline

Mostrar mensajes cacheados. Deshabilitar envio con explicacion. Se puede conservar un borrador local, pero nunca autoenviarlo al reconectar sin confirmacion del usuario.

---

## 30. Entrada por voz

Si existe soporte web:

- pedir permiso solo al pulsar microfono;
- mostrar grabacion activa;
- permitir cancelar;
- presentar transcripcion antes de enviar;
- no enviar audio en segundo plano;
- manejar permiso denegado;
- ofrecer texto siempre.

No asumir disponibilidad uniforme en todos los navegadores. El componente no debe desaparecer dejando un hueco ni bloquear chat.

---

## 31. Actividad y versiones

### 31.1. Actividad

Todos los miembros autorizados ven:

- actor;
- accion;
- recurso;
- fecha;
- agrupaciones;
- cursor para cargar mas.

Usar el contrato de Fase 7. No recrear actividad a partir de mensajes WebSocket presentes solo en memoria.

### 31.2. Versiones

Solo propietario/organizador ve la lista si esa es la politica definida en Fase 7.

Mostrar:

- numero;
- nombre;
- autor;
- fecha;
- tipo manual/respaldo;
- resumen de contenido;
- hash abreviado opcional.

No mostrar:

- snapshot JSON completo;
- boton restaurar;
- boton guardar version;
- controles administrativos.

Agregar texto breve `La restauracion esta disponible en escritorio`.

---

## 32. Estado de generaciones

Crear una vista de lectura:

- proyecto/diagrama fuente;
- revision utilizada;
- Spring Boot;
- Flutter;
- estado general;
- progreso por etapa;
- fecha de inicio/fin;
- diagnostico resumido;
- tamano de artefacto;
- expiracion de descarga si existe.

WebSocket o polling adaptativo actualiza ejecuciones activas.

### 32.1. Descargas

Si se permite descargar:

- accion explicita;
- mostrar nombre y tamano;
- advertir sobre datos moviles para archivos grandes;
- usar URL autorizada de corta duracion si aplica;
- no almacenar ZIP en cache offline;
- manejar cancelacion.

No iniciar nuevas generaciones desde movil.

---

## 33. Notificaciones en movil

Consumir la bandeja persistente de Fase 7.

### 33.1. Campana

- Badge actualizado.
- Acceso desde cabecera.
- Lista en bottom sheet/pantalla.
- Marcar leida.
- Marcar todas.
- Preferencias.

### 33.2. Deep links

Resolver descriptor estructurado:

```text
project -> detalle
diagram -> visor readonly
activity -> tab actividad
ai_conversation -> tab IA
generation -> detalle de generacion
version -> lista de versiones
```

Si el recurso no existe o el acceso fue revocado:

- marcar notificacion como leida si corresponde;
- mostrar mensaje seguro;
- navegar a proyectos;
- no revelar nombre/datos del recurso.

### 33.3. Sincronizacion

Leer una notificacion en movil debe reflejarse en escritorio mediante API y evento de usuario, o en la siguiente revalidacion.

---

## 34. Web Push en PWA

### 34.1. Activacion

No pedir permiso al cargar. Mostrar una accion contextual despues de explicar utilidad.

Estados:

```text
unsupported
default
denied
subscribing
subscribed
error
```

### 34.2. iOS y navegadores con soporte parcial

Detectar capacidad real. Cuando Push solo esta disponible en PWA instalada, explicar que primero se agregue a inicio. No mostrar instrucciones incorrectas en Android/desktop.

### 34.3. Click

El service worker:

1. Cierra notificacion.
2. Valida que el destino sea interno.
3. Busca una ventana del mismo origen.
4. La enfoca y navega, o abre una nueva.
5. Entrega `notification_id` a la app.
6. La app marca clicked/leida tras autenticar.

No construir `new URL` con un origen arbitrario recibido.

### 34.4. Renovacion

Al arrancar online:

- comprobar suscripcion existente;
- sincronizarla con backend si cambio;
- no crear varias por render;
- eliminar endpoints 404/410 segun Fase 7.

---

## 35. WebSocket y ciclo de vida movil

Los navegadores suspenden pestanas/PWA en segundo plano. Implementar una maquina de estados:

```text
idle
connecting
connected
backoff
suspended
offline
closed
```

### 35.1. Al ir al fondo

- No asumir que socket seguira vivo.
- Registrar ultima secuencia.
- Detener heartbeats innecesarios cuando el runtime se suspenda.

### 35.2. Al volver visible

1. Comprobar sesion.
2. Comprobar conectividad del backend.
3. Reconectar con backoff.
4. Enviar ultima secuencia.
5. Obtener backlog o `resync_required`.
6. Revalidar notificaciones y recursos activos.

### 35.3. Backoff

- Exponencial con jitter.
- Limite superior.
- Reinicio al recuperar red.
- Una sola conexion por proyecto/vista.
- Cancelacion al navegar o cerrar sesion.

No crear un socket en cada componente que necesita un dato.

---

## 36. Sincronizacion al recuperar conectividad

Crear un coordinador central:

```ts
syncCoordinator.revalidate({ reason: "online" | "resume" | "push" | "manual" })
```

Orden:

1. Sesion/usuario.
2. Contador de notificaciones.
3. Proyecto activo.
4. Revision del diagrama activo.
5. Conversacion activa.
6. Generaciones activas.
7. Actividad.

Evitar tormenta de solicitudes:

- deduplicar recursos;
- limitar concurrencia;
- cancelar respuestas antiguas;
- respetar `AbortController`;
- no sincronizar proyectos no visibles inmediatamente.

---

## 37. Estados de red

No confiar solo en `navigator.onLine`.

Definir:

```text
browser_offline
backend_reachable
backend_unreachable
session_expired
degraded
```

Un endpoint liviano autenticado o la propia consulta puede determinar reachability. No hacer ping agresivo.

Mensajes diferenciados:

- `Sin conexion de red`.
- `No se puede alcanzar el servidor`.
- `La sesion vencio`.
- `El motor de IA no esta disponible`.
- `WebSocket reconectando`.

Esto evita diagnosticar CORS, Ollama o backend detenido como una unica falla de Internet.

---

## 38. Estados y consistencia de datos

Cada recurso mostrado desde cache incluye metadata interna:

```ts
type ResourceState<T> = {
  data: T | null;
  source: "network" | "cache";
  cachedAt: string | null;
  stale: boolean;
  loading: boolean;
  errorCode: string | null;
};
```

No mezclar datos de revisiones diferentes sin indicarlo. Si detalle del proyecto es revision 12 y diagrama cacheado revision 9:

- mostrar diagrama como desactualizado;
- revalidar al conectar;
- no presentarlo como estado actual.

---

## 39. Responsive por componente

Auditar cada pantalla incluida:

- login;
- proyectos;
- proyecto;
- miembros;
- actividad;
- versiones;
- visor UML;
- IA;
- generaciones;
- notificaciones;
- perfil.

Para cada una verificar:

- 320px de ancho.
- 360px.
- 390px.
- 412px.
- 768px.
- orientacion horizontal.
- teclado abierto.
- texto al 200%.
- nombres largos.
- emails largos.
- estados vacios y errores.

No usar font-size dependiente del ancho de viewport. Permitir salto de linea y `min-width: 0`.

---

## 40. Touch targets y gestos

- Objetivos tactiles minimos 44x44.
- Separacion suficiente entre acciones destructivas y normales.
- No depender de hover.
- Menus abren por toque y teclado.
- Tooltips no contienen informacion indispensable.
- Swipe no reemplaza una accion visible.
- Pull-to-refresh solo si no interfiere con pan UML; puede omitirse.
- Evitar botones flotantes sobre barra inferior.
- Respetar safe areas.

---

## 41. Accesibilidad

Cumplir como minimo WCAG 2.1 AA en flujos incluidos.

- Landmarks correctos.
- Un `h1` por pantalla.
- Orden de foco.
- Focus visible.
- Dialogos con focus trap.
- Sheets anunciadas.
- Labels en controles.
- Iconos decorativos `aria-hidden`.
- Contraste en claro/oscuro.
- No depender de color.
- `prefers-reduced-motion`.
- `aria-live` para offline/reconexion sin repetir constantemente.
- Visor UML con alternativa textual de clases y relaciones.

La alternativa textual permite comprender el diagrama con lector de pantalla y sirve como fallback de rendimiento.

---

## 42. Tema visual

Mantener identidad actual sin convertirla en una pagina promocional.

- Superficies de trabajo sobrias.
- Cards solo para items repetidos.
- Radio maximo acorde al sistema existente.
- Paleta con contraste, sin saturar toda la app de un solo color.
- Tema claro y oscuro.
- Barra de estado y `theme-color` coherentes.
- Navegacion inferior estable.
- Tipografia legible.

No confundir el tema de la plataforma CASE con el tema Flutter que el usuario edita para su aplicacion generada.

---

## 43. Componentes sugeridos

```text
frontend/src/shared/layouts/
  AppLayout.tsx
  DesktopShell.tsx
  MobileShell.tsx
  MobileBottomNavigation.tsx
  MobileTopBar.tsx

frontend/src/core/pwa/
  PwaUpdatePrompt.tsx
  InstallPwaAction.tsx
  usePwaInstall.ts
  useAppSurface.ts
  useConnectivity.ts

frontend/src/core/offline/
  offlineDatabase.ts
  offlineRepository.ts
  offlinePolicy.ts
  syncCoordinator.ts

frontend/src/modules/gestion_proyectos_colaboracion/mobile/
  MobileProjectOverview.tsx
  MobileProjectTabs.tsx
  MobileMembersList.tsx
  MobileActivityFeed.tsx
  MobileVersionList.tsx

frontend/src/modules/modelado_uml_inteligente/mobile/
  MobileUmlViewer.tsx
  UmlViewerControls.tsx
  UmlClassDetailSheet.tsx
  UmlRelationshipDetailSheet.tsx
  UmlTextOutline.tsx

frontend/src/modules/notificaciones/
  MobileNotificationPanel.tsx
```

Adaptar nombres a la estructura real. No duplicar servicios existentes.

---

## 44. Contratos backend necesarios

Preferir endpoints existentes. Si las pantallas requieren demasiadas llamadas, crear un resumen delgado:

```http
GET /api/v1/projects/{project_id}/overview
```

Posible respuesta:

```json
{
  "project": {},
  "current_user_role": "EDITOR",
  "project_revision": 42,
  "diagram_count": 3,
  "member_count": 4,
  "latest_activity": [],
  "latest_generation": null,
  "unread_project_notifications": 2
}
```

No llamar al endpoint `mobile-overview`; es un resumen util tambien para escritorio.

Contratos requeridos:

- proyectos paginados;
- detalle;
- miembros;
- diagramas resumidos;
- snapshot de diagrama readonly;
- actividad por cursor;
- versiones resumidas autorizadas;
- conversacion por cursor;
- generaciones por cursor/estado;
- notificaciones;
- revision actual.

---

## 45. Optimizacion de API

- ETag o revision para GET de diagrama.
- `If-None-Match`/304 cuando encaje.
- Compresion HTTP.
- DTOs resumen sin snapshots pesados.
- Cursor en listas.
- Limites maximos.
- Campos opcionales con `include=` solo si existe patron consistente.
- Cancelacion cliente al cambiar ruta.
- No enviar todos los artefactos binarios.
- No incluir audit logs administrativos.

Una PWA movil no debe descargar el modelo completo de todos los proyectos al iniciar.

---

## 46. Seguridad

- Mismos permisos backend.
- No exponer acciones excluidas por endpoints inseguros.
- No incluir tokens en URL o subprotocolo visible en logs; mantener el mecanismo WebSocket ya endurecido.
- No almacenar token en service worker.
- No cachear respuestas privadas en Cache Storage compartida.
- Limpiar IndexedDB por usuario.
- Validar deep links.
- CSP compatible con PWA y API.
- HTTPS/WSS en produccion.
- No registrar conversaciones completas en consola.
- Ocultar detalles de recursos revocados.
- Limitar tamano de mensajes y snapshots.
- Sanitizar nombres/descripciones.

Revisar que el service worker no convierta una respuesta 401 en una respuesta cacheada de otro usuario.

---

## 47. Privacidad en dispositivos compartidos

Agregar una opcion visible para borrar datos offline.

Al cerrar sesion:

- purgar IndexedDB privada;
- limpiar stores en memoria;
- cerrar sockets;
- limpiar borradores de IA;
- conservar solo assets publicos del shell;
- no mostrar nombres de proyectos en pantalla de login.

La notificacion Push debe usar cuerpos discretos configurables si el sistema maneja proyectos sensibles.

---

## 48. Manejo de errores

Mapear codigos de dominio a mensajes claros:

```text
NETWORK_OFFLINE
BACKEND_UNREACHABLE
SESSION_EXPIRED
PROJECT_ACCESS_DENIED
PROJECT_NOT_FOUND
DIAGRAM_NOT_FOUND
RESOURCE_STALE
RESYNC_REQUIRED
AI_UNAVAILABLE
PUSH_UNSUPPORTED
PUSH_PERMISSION_DENIED
PWA_INSTALL_UNAVAILABLE
CACHE_UNAVAILABLE
```

No mostrar stack traces, Axios errors ni mensajes CORS crudos al usuario.

Acciones de recuperacion:

- reintentar;
- volver a proyectos;
- iniciar sesion;
- abrir datos cacheados;
- continuar en escritorio;
- borrar cache corrupta.

---

## 49. Instalacion PWA

Crear `usePwaInstall` que gestione:

- `beforeinstallprompt` cuando exista;
- app ya instalada;
- `display-mode: standalone`;
- instrucciones iOS separadas;
- ausencia de soporte;
- resultado accepted/dismissed.

No mostrar un modal invasivo al primer segundo. Ofrecer instalacion desde perfil/menu y, opcionalmente, una sugerencia discreta despues de uso significativo.

No afirmar que se instalo hasta verificar estado/evento disponible.

---

## 50. Service worker y notificaciones existentes

Actualmente el worker generado importa `push-notifications.js`. Conservar una unica fuente de listeners.

Revisar:

- que no se registren dos listeners `push`;
- que el archivo importado quede en build;
- que cambios de version invaliden correctamente;
- que `notificationclick` use deep link estructurado;
- que iconos raster existan;
- que la navegacion funcione con app cerrada;
- que no se abra una segunda ventana innecesaria;
- que el evento espere promesas mediante `event.waitUntil`.

Escribir pruebas unitarias para funciones puras de resolucion de deep links y pruebas manuales/controladas para worker.

---

## 51. Estado de instalacion y actualizacion

Mostrar estados en Perfil o Mas:

- Instalable.
- Instalada.
- Actualizacion disponible.
- Offline listo.
- Push habilitado/deshabilitado.
- Ultima sincronizacion.
- Tamano aproximado de datos offline si se puede obtener.

No usar texto tecnico como `service worker waiting` en la UI.

---

## 52. Rendimiento y presupuestos

Definir presupuestos verificables para produccion:

- Shell inicial sin JointJS cuando no se abre UML.
- Lazy-load de paginas pesadas.
- Chunks por modulo.
- Sin imagenes decorativas pesadas.
- Tiempo de interaccion razonable en red movil simulada.
- Cero layout shift importante en navegacion.
- Memoria estable al abrir/cerrar varios diagramas.

Analizar bundle con la herramienta compatible con Vite solo si es necesaria. No incorporar analizador en produccion.

Objetivos orientativos, ajustables con evidencia:

- JS inicial comprimido menor de 300 KB cuando sea viable.
- Ruta del visor cargada bajo demanda.
- Lista de proyectos util antes de cargar actividad secundaria.
- Cache offline acotada por usuario y TTL.

---

## 53. Lazy loading

Usar `React.lazy`/`Suspense` para:

- visor JointJS;
- conversacion IA si es pesada;
- detalle de generaciones;
- panel de versiones;
- pantallas administrativas de escritorio.

El fallback debe tener dimensiones estables. No mostrar un spinner de pantalla completa para cada tab.

Preload del visor solo al mostrar lista de diagramas o ante intencion clara, no al login.

---

## 54. Imagenes, iconos y fuentes

- Usar iconos Lucide existentes.
- Generar iconos PWA raster a partir de identidad actual con pipeline reproducible.
- No cargar fuentes remotas requeridas para operar offline.
- Preferir system fonts o fuentes locales precacheadas.
- Comprimir imagenes.
- Definir dimensiones para evitar saltos.
- Incluir `apple-touch-icon`.

No usar un logo borroso ampliado para 512x512.

---

## 55. Orientacion y teclado virtual

### 55.1. Orientacion

- Portrait para navegacion general.
- Landscape permitido y util para UML.
- No bloquear orientacion desde manifiesto salvo evidencia.
- Reajustar viewport del diagrama sin perder seleccion.

### 55.2. Teclado

- La caja de chat permanece visible.
- La barra inferior no tapa input.
- Usar `visualViewport` con fallback cuando corresponda.
- Evitar scroll jumps.
- Restaurar posicion al cerrar teclado.

Probar Android Chrome e iOS Safari/PWA manualmente cuando haya dispositivo.

---

## 56. Integracion con compartir y archivos

No declarar `share_target` ni `file_handlers` en el manifiesto si no se implementan de extremo a extremo.

Se puede usar Web Share API para compartir un enlace interno al proyecto/diagrama cuando:

- el usuario tiene acceso;
- el enlace no contiene token;
- existe fallback para copiar enlace;
- el receptor igualmente debe autenticarse.

Importacion de fotos/XMI desde movil permanece excluida.

---

## 57. Telemetria y observabilidad

Medir sin datos sensibles:

- instalaciones sugeridas/aceptadas cuando API lo permita;
- errores de registro del service worker;
- version activa del worker;
- uso online/offline;
- fallos de IndexedDB;
- cache hit de lectura;
- tiempo de carga de proyectos;
- tiempo de render UML;
- reconexiones WebSocket;
- deep links fallidos;
- permisos push denegados;
- errores de update.

No enviar:

- contenido de diagramas;
- mensajes IA;
- nombres de proyectos;
- tokens;
- endpoints de suscripcion;
- correos completos.

---

## 58. Pruebas unitarias de PWA

Cubrir:

1. Deteccion de superficie.
2. Deteccion standalone.
3. Estado online/offline.
4. Resolucion de variables HTTPS/WSS.
5. Deep links permitidos.
6. Rechazo de URL externa.
7. Estado de instalacion.
8. Prompt de actualizacion.
9. Politica de cache por tipo de recurso.
10. Namespace de usuario.
11. Purga al logout.
12. TTL y datos stale.
13. Migracion de esquema IndexedDB.
14. Recurso corrupto descartado.
15. Borrador IA no enviado automaticamente.

Mockear APIs del navegador de forma controlada.

---

## 59. Pruebas del visor UML

- Readonly no mueve clases.
- Readonly no renombra.
- Tecla Delete no muta.
- No se crean relaciones.
- Tap selecciona clase.
- Tap selecciona relacion.
- Pinch cambia escala dentro de limites.
- Pan cambia viewport.
- Ajustar calcula bounds.
- Resize conserva encuadre valido.
- Restauracion invalida snapshot.
- Cache muestra diagrama offline.
- Alternativa textual contiene clases y relaciones.
- Textos largos no desbordan nodos.
- Metodo vacio no muestra metodo fantasma.

Verificar que pruebas del editor en modo `edit` siguen pasando.

---

## 60. Pruebas de conversacion movil

- Carga mensajes por cursor.
- Recibe mensaje WebSocket una vez.
- Reconexion no duplica.
- Envio usa idempotency key.
- Offline deshabilita envio.
- Borrador se conserva localmente.
- Reconectar no autoenvia.
- Propuesta de edicion muestra `Continuar en escritorio`.
- Consulta informativa responde normalmente.
- Referencia a clase abre ficha/visor.
- Remocion de acceso cierra conversacion.

---

## 61. Pruebas de notificaciones

- Badge refleja no leidas.
- Bandeja carga por cursor.
- Marcar leida es optimista con rollback si falla.
- Click resuelve proyecto.
- Click resuelve diagrama.
- Click resuelve IA.
- Click resuelve generacion.
- Recurso revocado cae a proyectos.
- Push no soportado degrada a bandeja.
- Permiso denegado no se vuelve a pedir automaticamente.
- Abrir desde app cerrada funciona.
- Leer en movil se sincroniza con escritorio.

---

## 62. Pruebas responsive

Usar Playwright con viewports/dispositivos representativos:

```text
320x568
360x800
390x844
412x915
768x1024
1024x768
1440x900
```

Capturar al menos:

- login;
- proyectos;
- detalle;
- visor con diagrama pequeno;
- visor con diagrama grande;
- IA con teclado simulado;
- actividad;
- notificaciones;
- offline;
- update disponible.

Comprobar automaticamente:

- ausencia de overflow horizontal global;
- elementos dentro del viewport;
- targets tactiles;
- barra inferior no tapa contenido;
- sheets no se superponen;
- canvas no esta en blanco.

---

## 63. Pruebas PWA automatizadas y manuales

### 63.1. Build real

```powershell
npm run build
npm run preview -- --host 0.0.0.0
```

No evaluar service worker solamente con `npm run dev`.

### 63.2. Lighthouse

Ejecutar auditorias de:

- PWA/installability segun capacidades vigentes.
- Performance.
- Accessibility.
- Best practices.

No perseguir una puntuacion ocultando funcionalidad. Documentar resultados y causas.

### 63.3. Offline

1. Cargar online.
2. Abrir proyectos y un diagrama.
3. Instalar/controlar worker.
4. Desconectar red.
5. Recargar ruta profunda.
6. Ver datos cacheados con fecha.
7. Intentar IA y verificar bloqueo honesto.
8. Reconectar.
9. Revalidar sin duplicados.

### 63.4. Update

1. Servir build A.
2. Abrir PWA.
3. Servir build B.
4. Detectar update.
5. Posponer.
6. Actualizar.
7. Verificar version B sin loop.

---

## 64. Pruebas en dispositivos reales

Cuando esten disponibles:

- Android Chrome instalado.
- Android Chrome navegador.
- iPhone Safari.
- iPhone PWA agregada a inicio.
- Tablet portrait/landscape.

Verificar:

- safe areas;
- teclado;
- push donde exista soporte;
- instalacion;
- icono;
- splash/background;
- back button Android;
- retorno desde notificacion;
- suspension/reanudacion;
- pinch/pan;
- memoria con diagrama grande.

Registrar version de SO/navegador, porque capacidades PWA y Push cambian.

---

## 65. Pruebas de seguridad

- Cache no cruza usuarios.
- Logout purga datos.
- 401 no devuelve cache como si fuera autorizada sin aviso.
- Recurso revocado se elimina.
- Deep link externo se rechaza.
- Token no aparece en cache, manifiesto ni logs.
- Service worker no intercepta origen ajeno.
- HTML inyectado se presenta como texto.
- PWA no expone admin por ocultar sidebar.
- Endpoints siguen validando permisos.
- Push payload no contiene informacion excesiva.

---

## 66. Pruebas de regresion de escritorio

Ejecutar y verificar:

- Sidebar de escritorio.
- Topbar.
- Editor UML completo.
- Drag/rename/relaciones en modo edit.
- Generacion.
- Editor de estilos.
- IA y voz.
- Versiones/restauracion.
- Administracion.
- Reportes.
- Perfil.
- Push.
- Temas claro/oscuro.

La extraccion del renderer readonly es un punto de alto riesgo: probar explicitamente que no deshabilito callbacks del editor desktop.

---

## 67. Casos limite

- Primera apertura sin red.
- PWA nunca instalada.
- Worker antiguo controlando build nuevo.
- IndexedDB bloqueada o llena.
- Storage evicted por el sistema.
- Sesion expirada offline.
- Usuario cambia de cuenta.
- Proyecto eliminado mientras estaba cacheado.
- Rol reducido mientras la app estaba suspendida.
- Diagrama restaurado desde escritorio.
- Diagrama sin clases.
- Diagrama con 100 clases.
- Clase con nombre muy largo.
- Relacion sin etiqueta.
- Association class.
- Chat con cientos de mensajes.
- Push recibido con app abierta.
- Push recibido con app cerrada.
- Dos pushes con mismo tag.
- Backend disponible pero Ollama detenido.
- API disponible pero WebSocket bloqueado.
- Rotacion durante pinch.
- Teclado abierto al recibir mensaje.
- Notificacion a recurso sin acceso.

Cada caso debe tener comportamiento definido, no solo ausencia de crash.

---

## 68. Plan de implementacion en una pasada

Aunque se ejecute por bloques, no entregar una PWA a medias.

Orden recomendado:

1. Auditar rutas, shell, PWA y contratos.
2. Definir `AppSurface` y politica de capacidades.
3. Extraer `DesktopShell` sin cambiar apariencia.
4. Implementar `MobileShell` y overlays coordinados.
5. Endurecer manifiesto, iconos y update prompt.
6. Definir estrategia Workbox.
7. Implementar IndexedDB y politica offline.
8. Adaptar autenticacion/arranque offline.
9. Crear lista y detalle movil.
10. Extraer renderer UML readonly.
11. Implementar gestos y fichas.
12. Adaptar actividad/versiones.
13. Adaptar conversacion IA.
14. Crear estado de generaciones.
15. Integrar bandeja y deep links.
16. Endurecer WebSocket para lifecycle movil.
17. Optimizar chunks y red.
18. Ejecutar pruebas responsive/PWA/offline.
19. Ejecutar regresion desktop.
20. Documentar instalacion, limites y topologias.

---

## 69. Estrategia de despliegue

### 69.1. Build

- Generar assets con hash.
- Incluir manifiesto e iconos.
- Verificar worker generado.
- No subir `.env` real.

### 69.2. Headers

Configurar:

- `manifest.webmanifest`: cache control razonable.
- service worker: revalidacion frecuente/no cache inmutable.
- assets con hash: cache larga e immutable.
- `index.html`: revalidacion.
- CSP y security headers.

### 69.3. Rollback

Un rollback de hosting debe considerar que clientes conservan workers previos. Mantener compatibilidad de contratos y probar activacion de un build anterior/nuevo.

### 69.4. Deep routes

Configurar rewrite SPA sin interceptar APIs si comparten dominio.

---

## 70. Documentacion obligatoria

Crear en `docs/segundo_parcial` o ubicacion definida:

- Arquitectura PWA.
- Matriz de funciones movil/escritorio.
- Matriz online/offline.
- Instalacion Android.
- Instalacion iOS.
- Configuracion Vercel/hosting.
- Configuracion backend HTTPS/WSS.
- Uso en red local.
- Significado de `127.0.0.1` desde telefono.
- Politica de cache privada.
- Borrado de datos offline.
- Prueba de service worker con build.
- Diagnostico de Web Push.
- Diagnostico de actualizaciones.
- Resultados de dispositivos probados.

La documentacion no debe asegurar soporte que no fue verificado.

---

## 71. Prohibiciones explicitas

No hacer lo siguiente:

- Crear una segunda aplicacion movil.
- Generar un Flutter para la propia plataforma CASE.
- Duplicar endpoints solo con prefijo `/mobile`.
- Mostrar el editor completo encogido.
- Permitir drag accidental en readonly.
- Ocultar herramientas solo con CSS y dejar handlers activos.
- Cachear respuestas autenticadas en Workbox sin aislamiento.
- Cachear tokens.
- Autoenviar mutaciones al reconectar.
- Afirmar que la IA funciona offline.
- Afirmar que Web Push llega sin conectividad.
- Usar `127.0.0.1` para acceder desde otro dispositivo.
- Pedir permiso Push al cargar.
- Registrar dos service workers.
- Forzar actualizacion durante una accion.
- Abrir URLs arbitrarias desde push.
- Descargar ZIP en segundo plano.
- Restaurar versiones desde movil.
- Iniciar generacion pesada desde movil.
- Duplicar conversaciones.
- Romper escritorio para simplificar responsive.

---

## 72. Criterios de aceptacion funcional

La fase se acepta solo si:

1. La PWA es instalable con iconos correctos.
2. Una ruta profunda recarga correctamente.
3. La PWA instalada abre en standalone.
4. El shell carga offline despues de sincronizar.
5. Proyectos cacheados se ven offline con fecha.
6. Un diagrama cacheado se ve offline en readonly.
7. No se puede editar UML desde movil reducido.
8. Pan y pinch funcionan.
9. Ajustar muestra todo el diagrama.
10. La ficha muestra atributos, metodos y relaciones.
11. Actividad y versiones respetan roles.
12. Restaurar version no aparece en movil.
13. La conversacion es la misma que en escritorio.
14. Una solicitud estructural queda pendiente para escritorio.
15. Generaciones se consultan pero no se inician.
16. Notificaciones abren el destino correcto.
17. Push degrada a bandeja cuando no esta disponible.
18. Volver del fondo revalida sin duplicados.
19. Logout elimina datos privados offline.
20. Desktop conserva todas sus capacidades.
21. No hay overflow horizontal incoherente.
22. Navegacion y sheets no se superponen.
23. Teclado no tapa chat.
24. Las pruebas de build real, offline y responsive pasan.

---

## 73. Criterios de calidad tecnica

- Un solo frontend.
- Contratos compartidos.
- Service worker controlado.
- Manifiesto completo.
- Iconos raster y maskable.
- Cache privada aislada.
- Datos versionados en IndexedDB.
- Reconexiones idempotentes.
- Renderer readonly real.
- Lazy loading.
- Deep links cerrados.
- Permisos backend intactos.
- Accesibilidad AA en flujos principales.
- Sin secretos.
- Sin regresiones desktop.
- Documentacion verificable.

---

## 74. Checklist de revision

- [ ] Existe un solo registro de service worker.
- [ ] El manifiesto pasa validacion.
- [ ] Existen iconos 192, 512, maskable y Apple.
- [ ] El worker no cachea API privada en Cache Storage.
- [ ] IndexedDB separa usuarios.
- [ ] Logout purga cache privada.
- [ ] Offline muestra ultima sincronizacion.
- [ ] IA offline esta deshabilitada honestamente.
- [ ] No se autoenvian borradores.
- [ ] `JointUmlCanvas` readonly no muta.
- [ ] Pan/pinch estan probados.
- [ ] Existe alternativa textual UML.
- [ ] Versiones no permiten restaurar en movil.
- [ ] Generaciones no se inician en movil.
- [ ] Deep links no admiten origen externo.
- [ ] Push no se solicita automaticamente.
- [ ] WebSocket recupera secuencia.
- [ ] Restauracion remota invalida visor.
- [ ] Barra inferior respeta safe area.
- [ ] Sheets no se apilan.
- [ ] Teclado no tapa input.
- [ ] Build desktop sigue funcionando.
- [ ] No hay IPs fijas.
- [ ] `.env` real no se versiona.

---

## 75. Evidencia de entrega

Presentar al finalizar:

1. Inventario de archivos modificados.
2. Diagrama breve de shell, worker, API e IndexedDB.
3. Manifiesto final.
4. Estrategias Workbox finales.
5. Matriz online/offline implementada.
6. Matriz movil/escritorio implementada.
7. Evidencia de cache aislada por usuario.
8. Capturas de viewports principales.
9. Video/captura de pan y pinch si es posible.
10. Evidencia de notificacion y deep link.
11. Evidencia de suspension/reconexion.
12. Reporte de Lighthouse.
13. Pruebas automatizadas ejecutadas.
14. Dispositivos reales probados.
15. Regresiones de escritorio ejecutadas.
16. Limitaciones residuales.

No declarar soporte iOS Push, instalacion u offline completo si no se verifico en un entorno compatible.

---

## 76. Definicion de terminado de la Fase 8

La Fase 8 esta terminada cuando CASE Inteligente funciona como una PWA instalable y movil de consulta, reutilizando el sistema existente sin crear un producto paralelo. El usuario puede iniciar sesion, consultar proyectos y miembros, recorrer diagramas UML en solo lectura, revisar actividad y versiones permitidas, conversar con la IA, observar generaciones y abrir notificaciones, con una experiencia tactil clara y sin desbordamientos.

El flujo final debe demostrar:

```text
abrir o instalar PWA
        -> autenticar con los mismos permisos
        -> consultar proyectos
        -> abrir un proyecto
        -> revisar actividad y miembros
        -> abrir diagrama readonly
        -> pan / pinch / ajustar / inspeccionar clase
        -> conversar con la IA compartida
        -> consultar generaciones
        -> recibir notificacion
        -> abrir deep link correcto
        -> suspender y reanudar
        -> recuperar secuencia sin duplicados
        -> perder red
        -> consultar datos sincronizados
        -> reconectar y revalidar
        -> volver a escritorio sin ninguna regresion
```

Solo despues de verificar este flujo con build de produccion, viewports moviles y regresion desktop se puede pasar a la Fase 9 de pruebas integrales y endurecimiento final.
