# PROMPT FASE 6: EDITOR VISUAL Y PREVISUALIZACION FLUTTER

## 0. Instruccion maestra

Implementar la Fase 6 de la segunda parte de CASE Inteligente: completar el editor de estilos Flutter y convertir la previsualizacion actual en una representacion funcional, persistente y verificable del proyecto Flutter que se descargara.

Esta fase es un editor de estilos y una previsualizacion. No es un constructor manual de pantallas, un editor de widgets libre ni un segundo generador Flutter. La estructura funcional de listas, detalles, formularios y acciones proviene del `GenerationPlan` y `ui_manifest.json` de la Fase 5. El usuario modifica la apariencia dentro de opciones soportadas; no recrea toda la aplicacion.

La misma configuracion normalizada debe alimentar:

- La previsualizacion React.
- El manifiesto visual.
- Las plantillas Flutter.
- El ZIP generado.
- Los snapshots del proyecto.
- Los presets personalizados.

No permitir que el preview muestre un control, estilo o comportamiento que el generador no produzca realmente.

---

## 1. Resultado funcional buscado

Al finalizar:

1. El tema se carga y guarda por proyecto.
2. Dos colaboradores autorizados ven la misma configuracion confirmada.
3. El usuario edita colores, tipografia, botones, campos, cards y navegacion.
4. Existen tema claro y oscuro.
5. El preview usa entidades y metodos reales del diagrama seleccionado.
6. Se pueden inspeccionar lista, detalle, formulario, filtros y acciones de negocio.
7. Los controles corresponden a los contratos de Fase 4 y Fase 5.
8. Los cambios validos se reflejan inmediatamente en un borrador visual.
9. Guardar persiste la configuracion normalizada.
10. El generador Flutter usa esa configuracion persistida o el borrador confirmado enviado explicitamente.
11. El ZIP contiene exactamente los tokens y recetas soportados mostrados.
12. Los presets del sistema y personalizados se pueden aplicar sin perder control del borrador.
13. Configuraciones invalidas se corrigen a defaults seguros con diagnosticos visibles.
14. Contraste, textos largos, escalado de texto y desbordamientos se verifican.
15. La previsualizacion funciona en anchos moviles y escritorio.
16. Las pruebas de fidelidad detectan divergencias entre React y Flutter.

---

## 2. Alineacion obligatoria entre fases

### Fase 1

Reutilizar:

- `FlutterThemeSettings`.
- Tabla `flutter_theme_settings`.
- Endpoints de lectura y escritura por proyecto.
- `ProjectSnapshotV2.flutter_theme`.
- Evento `FLUTTER_THEME_UPDATED`.
- Convenciones de permisos, auditoria y JSONB versionado.

### Fase 2 y Fase 3

La IA colaborativa puede recomendar ajustes de accesibilidad o estilo, pero no crea una segunda configuracion ni persiste directamente. Las propuestas pasan por acciones confirmables, permisos y el mismo servicio del editor.

### Fase 4

Consumir contratos Flutter de metodos:

- `interaction`.
- `placement`.
- `fields`.
- `control`.
- `label`.
- `confirmation_required`.
- `refresh_targets`.
- `success_message`.

### Fase 5

Consumir:

- `GenerationPlan`.
- `ui_manifest.json`.
- Modulos reales.
- Pantallas reales.
- Acciones reales.
- Controles reales.
- Tema efectivo usado por el emisor Flutter.

### Entrega a Fase 7

Entregar una configuracion estable, serializable y versionada para snapshots. La Fase 7 endurecera restauracion, copia previa, bitacora y notificaciones.

---

## 3. Regla de fidelidad

La fidelidad se define en tres niveles:

1. **Contractual**: preview y Flutter contienen las mismas pantallas, acciones, campos, etiquetas y estados declarados.
2. **Tematica**: ambos usan los mismos tokens normalizados de color, tipografia, forma, densidad y componentes.
3. **Visual verificable**: capturas representativas no presentan divergencias sustanciales de jerarquia, espaciado, contraste, controles o desbordamiento.

React y Flutter usan motores de render distintos. No exigir igualdad byte a byte de pixeles. Si se usa comparacion de imagen, definir tolerancia documentada y excluir diferencias inevitables de rasterizacion de fuente o sistema operativo.

Una propiedad no se considera soportada hasta que:

- Existe en contrato.
- Se valida y persiste.
- Afecta al preview.
- Afecta a Flutter.
- Tiene prueba en ambos lados.

---

## 4. Precondiciones

Antes de implementar, verificar:

- La entidad `FlutterThemeSettings` existe o completar Fase 1.
- GET/PUT de tema verifican membresia y rol.
- El snapshot puede transportar `flutter_theme`.
- La Fase 5 produce `ui_manifest.json` desde el plan comun.
- El generador Flutter centraliza `ThemeData` y widgets compartidos.
- El preview inicial actual sigue funcionando.
- Los presets actuales se identifican como temporales o de sistema.
- Las pruebas del tema actual pasan.
- El editor puede seleccionar proyecto, diagrama y transformacion.

No construir una nueva previsualizacion basada en datos ficticios si ya existe manifiesto real.

---

## 5. Alcance exacto

- Contrato de tema version 2.
- Compatibilidad con tema version 1.
- Persistencia y concurrencia optimista.
- Tema claro y oscuro.
- Paletas y colores semanticos.
- Tipografia soportada y realmente incluida.
- Formas y radios.
- Densidad y espaciado.
- Estilos de botones.
- Estilos de campos.
- Estilos de cards/list items.
- Estilo de navegacion.
- Estados visuales.
- Presets del sistema.
- Presets personalizados compartidos por proyecto.
- Preview impulsado por `ui_manifest`.
- Selector de modulo, pantalla, accion, modo y dispositivo.
- Preview de lista, detalle, formulario, filtros y dialogos.
- Validacion de contraste y overflow.
- Sincronizacion colaborativa.
- Integracion con generador y snapshots.
- Pruebas unitarias, de componentes, visuales y Flutter golden.
- Documentacion completa.

---

## 6. Fuera de alcance

- Arrastrar widgets libremente.
- Crear pantallas no derivadas del modelo funcional.
- Cambiar rutas o DTO desde el editor visual.
- Editar reglas de negocio.
- Escribir CSS o Dart libre.
- Cargar paquetes Flutter arbitrarios.
- Permitir fuentes remotas no controladas.
- Generar logotipos o imagenes automaticamente.
- Implementar la restauracion completa de Fase 7.
- Redisenar la PWA movil de Fase 8.

---

## 7. Herramientas y tecnologias

### Frontend CASE

- React y TypeScript.
- Zustand o estado existente para borrador local.
- Axios/servicio HTTP existente.
- Cliente WebSocket de Fase 3.
- Tailwind y estilos existentes.
- Lucide para iconos.
- Vitest y React Testing Library.
- `@playwright/test` para pruebas de viewport y capturas si se incorpora en esta fase.

### Backend

- FastAPI.
- Pydantic 2.
- SQLAlchemy 2.
- PostgreSQL JSONB.
- Alembic.
- Servicio de proyecto, membresia, auditoria y eventos.
- Pytest.

### Flutter generado

- Flutter Material 3.
- `ThemeData`, `ColorScheme`, `TextTheme` y temas de componentes.
- `flutter_test`.
- Golden tests para componentes/pantallas representativas.
- Assets de fuentes solo cuando se incluyan realmente en `pubspec.yaml`.

### Contratos compartidos

- JSON Schema versionado.
- Fixtures canonicos JSON.
- `ui_manifest.json` de Fase 5.
- Normalizador autoritativo backend con implementacion TypeScript conforme por fixtures.

---

## 8. Linea base actual

Ya existe:

- `FlutterThemeConfig` version inicial.
- Cinco colores.
- Una familia tipografica.
- Radio global.
- Boton `filled`, `outline` o `tonal`.
- Densidad `compact`, `normal` o `comfortable`.
- Presets visuales locales en React.
- Preview movil basico.
- Normalizacion defensiva en el analizador Flutter.
- `AppTheme` y `PrimaryActionButton` generados.
- Pruebas que verifican tokens principales.

Brechas:

- El tema no debe depender solo del estado local de `GenerationPage`.
- La vista actual usa contenido mayormente fijo.
- No existen claro/oscuro completos.
- Falta persistencia real/presets personalizados completos.
- Faltan campos, cards y navegacion configurables.
- La familia puede declararse sin que el archivo de fuente exista.
- Hay logica de normalizacion duplicada.
- Falta validacion visual automatizada.

---

## 9. Fuente unica de verdad visual

Crear un artefacto versionado, por ejemplo:

```text
contracts/flutter_theme_v2.schema.json
contracts/flutter_theme_defaults_v2.json
contracts/flutter_theme_conformance_cases.json
```

El backend es autoridad al guardar. El frontend puede normalizar para respuesta inmediata, pero debe demostrar conformidad usando exactamente los mismos fixtures.

El generador no aplica defaults propios diferentes. Recibe un tema ya normalizado o llama al mismo normalizador de dominio antes de construir `FlutterProject`.

No mantener tres listas independientes de colores, densidades o variantes.

---

## 10. Evolucion de esquema

Mantener `schema_version: 1` compatible y definir version 2.

Reglas:

- Leer v1 y adaptarlo a v2.
- Guardar nuevos cambios como v2.
- No mutar silenciosamente el JSON historico de un snapshot.
- Una version futura desconocida produce error claro.
- Defaults son deterministas.
- Campos desconocidos se rechazan en escritura normal.
- Presets se migran al aplicar, no se reescriben todos automaticamente.

---

## 11. Contrato `FlutterThemeConfigV2`

Ejemplo:

```json
{
  "schema_version": 2,
  "mode": "system",
  "light": {
    "primary": "#0F766E",
    "on_primary": "#FFFFFF",
    "secondary": "#2563EB",
    "on_secondary": "#FFFFFF",
    "background": "#F8FAFC",
    "on_background": "#0F172A",
    "surface": "#FFFFFF",
    "on_surface": "#0F172A",
    "error": "#B91C1C",
    "on_error": "#FFFFFF",
    "outline": "#64748B"
  },
  "dark": {
    "primary": "#5EEAD4",
    "on_primary": "#042F2E",
    "secondary": "#93C5FD",
    "on_secondary": "#172554",
    "background": "#020617",
    "on_background": "#E2E8F0",
    "surface": "#0F172A",
    "on_surface": "#E2E8F0",
    "error": "#FCA5A5",
    "on_error": "#450A0A",
    "outline": "#94A3B8"
  },
  "typography": {
    "font_family": "Roboto",
    "heading_font_family": "Roboto",
    "scale": "normal",
    "weight": "regular"
  },
  "shape": {
    "button_radius": 8,
    "input_radius": 8,
    "card_radius": 8,
    "dialog_radius": 8
  },
  "components": {
    "button_style": "filled",
    "input_style": "outline",
    "card_style": "outlined",
    "navigation_style": "bottom_bar",
    "density": "normal",
    "show_field_labels": true
  }
}
```

Usar nombres definitivos coherentes en Pydantic y TypeScript. El ejemplo no autoriza campos adicionales.

---

## 12. Compatibilidad v1 a v2

Mapeo:

- `primary_color` -> `light.primary`.
- `secondary_color` -> `light.secondary`.
- `background_color` -> `light.background`.
- `surface_color` -> `light.surface`.
- `button_color` -> color del componente primario o token documentado.
- `font_family` -> `typography.font_family` y heading por defecto.
- `border_radius` -> todos los radios iniciales.
- `button_style` -> `components.button_style`.
- `density` -> `components.density`.

Calcular colores `on_*` mediante defaults seguros, no concatenando alfa como sustituto de contraste. Generar paleta oscura mediante preset seguro solo durante adaptacion; luego persistir valores explicitos.

---

## 13. Modos de tema

Valores:

- `light`.
- `dark`.
- `system`.

Flutter:

- `theme` usa tema claro.
- `darkTheme` usa tema oscuro.
- `themeMode` usa configuracion elegida.

Preview:

- Permite alternar claro/oscuro sin cambiar necesariamente el valor persistido de `mode`.
- Indica el modo inspeccionado y el modo por defecto.
- No mezcla tokens de ambos modos.

---

## 14. Colores semanticos

Cada paleta debe incluir:

- `primary` y `on_primary`.
- `secondary` y `on_secondary`.
- `background` y `on_background`.
- `surface` y `on_surface`.
- `error` y `on_error`.
- `outline`.

Opcionales solo si se implementan en ambos motores:

- `surface_variant`.
- `success`.
- `warning`.
- `info`.

No permitir que un solo color controle fondo, boton, texto y borde de forma accidental. Usar funciones semanticas.

---

## 15. Entrada de colores

Cada color editable usa:

- Swatch visual.
- Input hexadecimal.
- Selector nativo de color como apoyo.
- Etiqueta semantica.
- Muestra de contraste.
- Mensaje de error.

Validar `#RRGGBB`. Normalizar a mayusculas. No guardar alfa en v2 inicial salvo que Flutter y preview lo soporten de forma equivalente.

No depender unicamente del color para comunicar error o seleccion.

---

## 16. Contraste

Calcular luminancia relativa y relacion de contraste para:

- `primary/on_primary`.
- `secondary/on_secondary`.
- `background/on_background`.
- `surface/on_surface`.
- `error/on_error`.
- Texto de boton segun variante.
- Labels y bordes relevantes.

Umbrales iniciales:

- 4.5:1 para texto normal.
- 3:1 para texto grande y componentes graficos esenciales.

La UI muestra diagnostico accionable y una sugerencia segura. Un par principal usado para texto (`primary/on_primary`, `secondary/on_secondary`, `background/on_background`, `surface/on_surface` y `error/on_error`) por debajo de 4.5:1 bloquea guardar. Un borde o componente grafico esencial por debajo de 3:1 tambien bloquea. Combinaciones secundarias no usadas por la receta activa pueden producir advertencia. No corregir el color elegido sin informar.

---

## 17. Tipografia

Campos soportados:

- Familia de cuerpo.
- Familia de encabezados.
- Escala discreta: `compact`, `normal`, `large`.
- Peso base: `regular`, `medium`.

No permitir tamanos arbitrarios por viewport. Mapear escala a una tabla fija de `TextTheme` y CSS del preview.

No usar letter spacing negativo. Mantener letter spacing cero salvo requisito real documentado.

---

## 18. Catalogo de fuentes

Definir un catalogo cerrado. Cada opcion incluye:

```json
{
  "id": "inter",
  "display_name": "Inter",
  "font_family": "Inter",
  "source": "bundled",
  "asset_paths": ["assets/fonts/Inter-Regular.ttf", "assets/fonts/Inter-Medium.ttf"],
  "license_file": "assets/fonts/OFL.txt",
  "weights": [400, 500]
}
```

Reglas:

- No mostrar una fuente como soportada si no se incluye realmente.
- Incluir licencia correspondiente.
- Declarar assets en `pubspec.yaml`.
- Preview carga el mismo archivo de fuente mediante `@font-face` o recurso local del frontend.
- Mantener fallback seguro.
- No descargar fuentes en tiempo de ejecucion.
- Funcionamiento offline del proyecto generado no depende de CDN.

Si inicialmente solo una fuente cumple esto, ofrecer solo esa y sistema hasta agregar assets correctamente.

---

## 19. Forma y radios

Separar:

- Radio de botones.
- Radio de campos.
- Radio de cards.
- Radio de dialogos.

Rango seguro inicial: `0..24`, salvo justificacion distinta basada en componentes Flutter. Cards no deben convertirse en capsulas por defecto.

La vista previa debe mostrar cada radio sobre el componente correspondiente. Flutter debe usar los mismos valores en temas de componente.

---

## 20. Densidad y espaciado

Valores:

- `compact`.
- `normal`.
- `comfortable`.

Cada valor mapea a una receta fija:

```json
{
  "compact": {"screen_padding": 12, "section_gap": 8, "field_height": 44},
  "normal": {"screen_padding": 16, "section_gap": 12, "field_height": 48},
  "comfortable": {"screen_padding": 20, "section_gap": 16, "field_height": 52}
}
```

Ajustar valores finales tras verificar Material y accesibilidad. Mantener areas tactiles suficientes incluso en compacto.

Preview y Flutter consumen la misma receta serializada o generada desde contrato.

---

## 21. Botones

Variantes primarias:

- `filled`.
- `outline`.
- `tonal`.

Estados que deben verse:

- Normal.
- Presionado/hover donde aplique.
- Focus.
- Deshabilitado.
- Cargando.
- Destructivo.

El editor muestra swatches y ejemplos, no solo texto. Flutter centraliza `PrimaryActionButton`, `SecondaryActionButton` y accion destructiva si se introduce.

No crear una configuracion por cada boton individual en esta fase.

---

## 22. Campos

`input_style` inicial:

- `outline`.
- `filled`.

Previsualizar:

- Texto.
- Numero.
- Fecha.
- Switch.
- Dropdown/selector de entidad.
- Error.
- Deshabilitado.

Propiedades compartidas:

- Radio.
- Colores de borde/fill.
- Label.
- Texto de ayuda/error.
- Densidad.

No permitir que el editor cambie el tipo de control definido por Fase 4.

---

## 23. Cards y elementos de lista

`card_style` inicial:

- `flat`.
- `outlined`.
- `elevated`.

Definir receta de:

- Fondo.
- Borde.
- Elevacion.
- Radio.
- Padding.
- Separacion.

No usar cards anidadas. El preview debe representar lista y detalle con la misma jerarquia que Flutter.

---

## 24. Navegacion

`navigation_style` inicial:

- `bottom_bar` para pocos modulos.
- `navigation_drawer` para varios modulos.
- `automatic` decide de forma determinista segun cantidad.

Definir umbral unico en contrato. Preview puede alternar viewport, pero no inventa una navegacion diferente.

Previsualizar:

- Elemento activo.
- Elementos inactivos.
- Iconos disponibles.
- Etiquetas largas.
- Overflow de cantidad.

Usar iconos Material/Lucide equivalentes por identificador semantico, no SVG manual aislado.

---

## 25. Estados visuales globales

El manifiesto y preview deben soportar:

- Loading.
- Empty.
- Error.
- Offline.
- Unauthorized.
- Success feedback.
- Confirmation dialog.

El editor permite inspeccionarlos; no necesita alterar su logica funcional.

Cada estado debe existir tambien en Flutter o excluirse del preview.

---

## 26. Presets del sistema

Definir presets inmutables en codigo/contrato:

- Profesional claro.
- Profesional oscuro.
- Academico.
- Alto contraste, solo si cumple pruebas.

Cada preset:

- Tiene ID estable.
- Tiene nombre.
- Tiene descripcion corta.
- Declara schema version.
- Contiene configuracion completa normalizada.
- Tiene miniatura generada desde tokens, no imagen enganosa.

Aplicar preset copia valores al borrador; no guarda automaticamente.

---

## 27. Presets personalizados

Como `FlutterThemeSettings` guarda solo el tema activo, crear entidad separada si no existe:

```text
FlutterThemePreset
id                  UUID PK
project_id          UUID FK projects.id NOT NULL ON DELETE CASCADE
name                VARCHAR(120) NOT NULL
config_json         JSONB NOT NULL
schema_version      INTEGER NOT NULL
created_by_user_id  UUID FK users.id NOT NULL
updated_by_user_id  UUID FK users.id NOT NULL
created_at          TIMESTAMPTZ NOT NULL
updated_at          TIMESTAMPTZ NOT NULL
```

Restricciones:

- Nombre unico por proyecto sin distinguir mayusculas.
- Limite de presets por proyecto.
- Solo miembros con edicion crean/modifican/eliminan.
- Todos los miembros leen.
- Aplicar no cambia el preset.
- Editar tema activo no modifica preset de origen.
- Eliminar preset no modifica tema activo.

No mezclar preset del sistema con filas editables.

---

## 28. Persistencia del tema activo

Usar `FlutterThemeSettings` uno a uno con proyecto.

Agregar `revision INTEGER NOT NULL DEFAULT 1` mediante migracion incremental si Fase 1 no lo incluyo.

Reglas:

- Proyecto antiguo recibe default v2 adaptado.
- GET no crea fila por simple lectura salvo patron establecido.
- PUT es idempotente para contenido igual.
- Mutacion incrementa revision.
- Guardar registra autor real.
- Respuesta devuelve tema normalizado y diagnosticos.
- Generador usa el tema activo persistido por defecto.
- Un override de generacion debe ser explicito, validado y quedar en manifiesto.

---

## 29. Concurrencia optimista

GET devuelve:

```text
ETag: "flutter-theme-revision-4"
```

PUT exige `If-Match`. Primera creacion usa `If-None-Match: *`.

Ante revision obsoleta:

- Responder 409.
- Incluir revision actual.
- No sobrescribir.
- Frontend conserva borrador.
- Ofrecer comparar, recargar o reaplicar manualmente.

No fusionar automaticamente dos paletas sin mostrar diferencias.

---

## 30. API del tema

Mantener rutas de Fase 1:

```text
GET /api/v1/projects/{project_id}/flutter-theme
PUT /api/v1/projects/{project_id}/flutter-theme
```

Agregar:

```text
POST /api/v1/projects/{project_id}/flutter-theme/validate
POST /api/v1/projects/{project_id}/flutter-theme/reset
GET  /api/v1/projects/{project_id}/flutter-theme/presets
POST /api/v1/projects/{project_id}/flutter-theme/presets
PUT  /api/v1/projects/{project_id}/flutter-theme/presets/{preset_id}
DELETE /api/v1/projects/{project_id}/flutter-theme/presets/{preset_id}
POST /api/v1/projects/{project_id}/flutter-theme/presets/{preset_id}/apply
```

`validate` no persiste. `reset` requiere confirmacion de UI y control de revision. `apply` actualiza tema activo en una transaccion, no el preset.

---

## 31. API de manifiesto de preview

Exponer el `ui_manifest` real de Fase 5:

```text
GET /api/v1/generation/transformations/{transformation_id}/ui-manifest
POST /api/v1/generation/preview-manifest
```

`GET` devuelve manifiesto ya asociado a una transformacion. `POST` puede ejecutar compilacion/preflight sin escribir ZIP para un diagrama/version seleccionada.

El manifiesto debe incluir `source_hash`, version y diagnosticos. El preview muestra si esta desactualizado respecto del diagrama.

---

## 32. Modelo `PreviewRenderModel`

Frontend deriva un modelo estable:

```ts
type PreviewRenderModel = {
  manifestVersion: number;
  sourceHash: string;
  theme: NormalizedFlutterThemeV2;
  modules: PreviewModule[];
  selectedModuleId: string | null;
  selectedScreen: "list" | "detail" | "form" | "filter";
  selectedState: "default" | "loading" | "empty" | "error" | "offline";
  colorMode: "light" | "dark";
  viewport: PreviewViewport;
};
```

No guardar este estado efimero en tema persistente.

---

## 33. Contenido real del preview

Usar:

- Nombres reales de entidades.
- Atributos reales.
- Acciones reales.
- Etiquetas reales.
- Controles reales.
- Relaciones reales.
- Ubicaciones reales.

Para valores de muestra, generar datos deterministas por tipo:

- Texto: valor legible basado en nombre de campo.
- Numero: valor dentro de rango.
- Fecha: fecha fija de fixture, no fecha actual cambiante.
- Booleano: valor fijo.
- Referencia: etiqueta construida con `display_fields`.

Los valores son solo datos visuales y deben marcarse internamente como preview. No usar datos reales del usuario ni llamar al backend generado.

---

## 34. Selector de contexto del preview

Controles:

- Modulo/entidad.
- Pantalla.
- Accion, cuando hay varias.
- Estado visual.
- Tema claro/oscuro.
- Dispositivo/viewport.
- Escala de texto.

Usar selects, tabs o controles segmentados segun cantidad. No llenar la interfaz de botones de texto equivalentes.

El contexto seleccionado no modifica semantica ni se persiste como parte del tema, salvo preferencia local opcional.

---

## 35. Viewports

Definir dimensiones estables, por ejemplo:

- Movil compacto: 360 x 800.
- Movil comun: 390 x 844.
- Movil amplio: 430 x 932.
- Tablet: 768 x 1024.
- Escritorio Flutter web: 1280 x 800.

El contenedor puede escalar visualmente para caber, pero el layout interno calcula con dimensiones logicas. Mostrar porcentaje de escala si no es 100%.

No escalar fuentes con ancho de viewport. Probar texto accesible por separado.

---

## 36. Preview de lista

Debe mostrar segun manifiesto:

- App bar.
- Navegacion.
- Titulo de entidad.
- Loading/empty/error.
- Elementos de lista o cards.
- Campos resumen reales.
- Acciones por elemento.
- Accion primaria/FAB.
- Filtros si existen.

Textos largos usan wrap o ellipsis acorde con Flutter. No ocultar overflow mediante recorte arbitrario diferente al ZIP.

---

## 37. Preview de detalle

Mostrar:

- Titulo e identidad.
- Atributos reales con labels.
- Fechas y booleanos formateados.
- Relaciones mediante etiqueta.
- Acciones `detail_primary_action`.
- Menu `detail_overflow_action`.
- Estados y confirmacion.

No agregar secciones que Flutter no genere.

---

## 38. Preview de formulario

Construir campos desde `FlutterFieldContract`:

- Texto.
- Multilinea.
- Entero.
- Decimal.
- Fecha.
- Fecha-hora.
- Switch.
- Selector de entidad.
- Select simple/multiple.
- Contexto oculto, que no se renderiza como editable.

Mostrar:

- Obligatorio.
- Helper/error.
- Campo deshabilitado.
- Boton principal.
- Loading de envio.
- Mensaje de exito/error.

No implementar logica real de guardado; la interaccion cambia estados de preview de forma controlada.

---

## 39. Preview de acciones de negocio

Una accion debe aparecer en su `placement` real:

- Lista principal.
- Item de lista.
- Detalle principal.
- Menu secundario.
- Filtro.
- Submit de formulario.

Al activarla en preview:

- Si requiere confirmacion, abrir dialogo.
- Si usa formulario, navegar al preview de formulario.
- Si es boton simple, mostrar secuencia de loading/exito simulada sin red.
- Si esta deshabilitada por permiso, mostrar el estado acordado.

No ejecutar endpoints del backend generado desde CASE.

---

## 40. Arquitectura de componentes React

Extraer la maqueta monolitica de `GenerationPage.tsx` a componentes, por ejemplo:

```text
FlutterStyleEditor/
  FlutterStyleEditor.tsx
  ThemeModeEditor.tsx
  ColorTokenEditor.tsx
  TypographyEditor.tsx
  ShapeEditor.tsx
  ComponentStyleEditor.tsx
  PresetManager.tsx
FlutterPreview/
  FlutterPreview.tsx
  PreviewToolbar.tsx
  DeviceFrame.tsx
  PreviewNavigator.tsx
  ListPreview.tsx
  DetailPreview.tsx
  FormPreview.tsx
  FilterPreview.tsx
  ConfirmationPreview.tsx
  PreviewState.tsx
```

Usar componentes compartidos solo cuando eliminen duplicacion real. No crear una abstraccion por cada etiqueta.

---

## 41. Arquitectura de normalizacion frontend

Crear funciones puras:

- `adaptThemeV1ToV2`.
- `normalizeThemeDraft`.
- `resolveColorModeTokens`.
- `resolveDensityRecipe`.
- `resolveTypographyRecipe`.
- `calculateContrast`.
- `buildPreviewRenderModel`.

Estas funciones consumen defaults/fixtures compartidos. No leer estado global internamente.

---

## 42. Estado del editor

Separar:

- `savedTheme`.
- `draftTheme`.
- `serverRevision`.
- `validationDiagnostics`.
- `selectedPresetId`.
- `isDirty`.
- `isSaving`.
- `conflict`.
- Estado efimero del preview.

Aplicar preset modifica solo `draftTheme`. Guardar persiste. Cancelar restaura `savedTheme`. Navegar con cambios sin guardar solicita confirmacion.

---

## 43. Flujo de usuario

1. Abrir Generacion/Estilo Flutter dentro de un proyecto.
2. Cargar tema persistido.
3. Cargar o compilar `ui_manifest` del diagrama.
4. Seleccionar modulo y pantalla.
5. Modificar tokens.
6. Ver preview inmediato.
7. Revisar diagnosticos.
8. Aplicar preset si desea.
9. Guardar tema.
10. Backend normaliza y devuelve revision.
11. Evento actualiza colaboradores.
12. Ejecutar generacion coordinada.
13. Manifiesto generado registra mismo tema/hash.

---

## 44. Diseno de la pantalla CASE

Layout escritorio:

- Toolbar superior compacta.
- Panel izquierdo de categorias de estilo.
- Preview central dominante.
- Panel contextual derecho para modulo/pantalla/estado, si el ancho lo permite.

Layout reducido:

- Tabs entre `Estilo` y `Preview`.
- Toolbar fija sin superponer contenido.
- Controles apilados.

No usar hero, marketing ni secciones en cards flotantes. Es una herramienta operativa densa. Evitar cards dentro de cards.

---

## 45. Controles del editor

- Colores: swatch + hexadecimal.
- Modo: control segmentado.
- Fuente: menu con muestra tipografica.
- Variante de boton/campo/card: selector visual o segmentado.
- Radios: slider con valor numerico y limites.
- Densidad: segmentado.
- Opciones booleanas: switch/checkbox.
- Presets: menu/lista con aplicar, guardar y eliminar.
- Reset: icono/comando con confirmacion.
- Undo/redo local: iconos si se implementa historial de borrador.

Agregar tooltips para iconos no obvios. Mantener dimensiones estables.

---

## 46. Accesibilidad del editor

- Labels asociados.
- Navegacion por teclado.
- Focus visible.
- No depender solo del color.
- Errores anunciables.
- Botones con nombre accesible.
- Dialogos con foco controlado.
- Selectores de color tambien editables por texto.
- Preview no atrapa teclado.
- Escala de texto de prueba 100%, 130% y 160%.

El editor debe seguir siendo usable en tema oscuro de CASE, independiente del tema Flutter inspeccionado.

---

## 47. Validacion backend

Pydantic debe validar:

- Schema version.
- Enum de modo.
- Colores.
- Familias del catalogo.
- Pesos disponibles.
- Escalas.
- Radios.
- Variantes.
- Densidad.
- Campos extra prohibidos.

Validacion cruzada:

- Familia y peso existen juntos.
- Tokens `on_*` contrastan o generan diagnostico.
- Preset usa version soportada.
- Tema dark no omite campos requeridos.
- Variante tiene receta Flutter y preview.

---

## 48. Normalizador autoritativo

Orden:

1. Detectar version.
2. Adaptar v1.
3. Completar campos ausentes con defaults v2.
4. Normalizar hex.
5. Limitar numeros.
6. Validar catalogos.
7. Calcular diagnosticos de contraste.
8. Serializar orden estable.

No sustituir silenciosamente una fuente invalida sin diagnostico. La API devuelve:

```json
{
  "theme": {},
  "revision": 4,
  "diagnostics": [],
  "normalized_fields": []
}
```

---

## 49. Integracion con Flutter `ThemeData`

Generar:

- `ColorScheme` claro.
- `ColorScheme` oscuro.
- `ThemeData` claro.
- `ThemeData` oscuro.
- `TextTheme`.
- `AppBarTheme`.
- `InputDecorationTheme`.
- `CardThemeData`.
- `FilledButtonThemeData`.
- `OutlinedButtonThemeData`.
- `FloatingActionButtonThemeData`.
- `SwitchThemeData`.
- `NavigationBarThemeData` o drawer equivalente.
- `DialogThemeData`.

Usar tokens, no colores repetidos en pantallas.

---

## 50. Component recipes compartidas

Crear recetas versionadas independientes del motor:

```json
{
  "button": {
    "variant": "filled",
    "radius_token": "button_radius",
    "foreground_token": "on_primary",
    "background_token": "primary"
  }
}
```

El preview traduce receta a CSS/React. Flutter traduce a `ButtonStyle`/ThemeData. Las plantillas no deciden otra variante.

Cubrir:

- Boton.
- Input.
- Card.
- Navegacion.
- Dialogo.
- Feedback.

---

## 51. Integracion con `ui_manifest`

El manifiesto debe contener identificadores, no JSX/Dart:

- Modulo.
- Pantalla.
- Campo.
- Tipo de control.
- Accion.
- Placement.
- Estado.
- Icono semantico.

Preview y generador consumen el mismo identificador. Si el preview no reconoce uno:

- Mostrar diagnostico de contrato.
- No reemplazar por un control aparentemente equivalente.
- Bloquear fidelidad hasta implementar ambos adaptadores.

---

## 52. Integracion con la generacion

La solicitud coordinada de Fase 5 debe:

- Usar tema persistido por defecto.
- Permitir override solo desde borrador validado y confirmado.
- Guardar tema efectivo completo en manifiesto.
- Guardar hash del tema.
- Guardar version del contrato.
- Generar `ui_manifest.json` con tema efectivo o referencia/hash.

La UI debe advertir si se genera con cambios de estilo sin guardar y ofrecer guardar o usar override explicito.

---

## 53. Fidelidad de fuentes

Para cada fuente:

- Preview carga asset real.
- Flutter incluye asset real.
- Pesos declarados existen.
- Fallback es equivalente.
- Golden test se ejecuta con assets.
- Licencia se incluye.

No basta con poner `fontFamily: 'Inter'`. Si el asset no existe, la opcion debe rechazarse o usar fuente del sistema explicitamente etiquetada.

---

## 54. Fidelidad de iconos

Definir catalogo semantico:

```text
add -> Plus / Icons.add
edit -> Pencil / Icons.edit
delete -> Trash2 / Icons.delete
search -> Search / Icons.search
save -> Save / Icons.save
```

La forma exacta puede variar por biblioteca, pero significado, ubicacion, label y accesibilidad deben coincidir.

No dibujar SVG manual si existe icono de biblioteca.

---

## 55. Textos largos y localizacion

Fixtures:

- Nombre de entidad largo.
- Label de accion largo.
- Campo con palabra larga.
- Mensaje de error multilinea.
- Nombre de opcion de relacion largo.

Reglas:

- Botones pueden crecer en altura o ajustar layout.
- No reducir fuente segun viewport.
- Cards no ocultan campos importantes.
- Dropdown usa expansion y ellipsis donde Flutter tambien lo hace.
- App bar no superpone acciones.
- Navegacion adapta labels.

Aunque la aplicacion sea inicialmente espanol, no incrustar anchos basados en una frase concreta.

---

## 56. Overflow y geometria

Probar:

- 360 px de ancho.
- Escala de texto 160%.
- Selectores con UUID/nombre largo.
- Cinco o mas acciones.
- Muchos campos.
- Teclado virtual simulado cuando aplique.
- Orientacion horizontal.

En Flutter, usar `Expanded`, `Flexible`, `Wrap`, scroll y constraints apropiados. En preview, reproducir la misma estrategia conceptual.

No ocultar banners de overflow en pruebas; tratarlos como fallo.

---

## 57. Presencia y colaboracion

Al guardar tema:

1. Validar revision.
2. Persistir.
3. Auditar.
4. Commit.
5. Emitir `FLUTTER_THEME_UPDATED`.

Payload:

```json
{
  "project_id": "uuid",
  "revision": 5,
  "schema_version": 2,
  "updated_by": {"user_id": "uuid", "display_name": "Usuario"},
  "changed_sections": ["light", "components.button_style"],
  "theme_hash": "sha256",
  "occurred_at": "ISO-8601"
}
```

No enviar tema completo por WebSocket si puede recuperarse por REST.

---

## 58. Conflictos colaborativos

Si llega evento remoto:

- Sin borrador local: recargar tema.
- Con borrador sin guardar: mostrar aviso y conservarlo.
- Permitir comparar secciones.
- Permitir descartar local y recargar.
- Permitir reaplicar cambios sobre revision nueva y revalidar.

No realizar last-write-wins silencioso.

---

## 59. Auditoria

Registrar:

- Tema creado.
- Tema actualizado.
- Tema restablecido.
- Preset creado/editado/eliminado/aplicado.
- Propuesta IA aceptada/rechazada.

Metadata:

- Revision anterior/nueva.
- Secciones modificadas.
- Preset ID.
- Hash anterior/nuevo.
- Schema version.
- Correlation ID.

No guardar snapshots completos del tema en cada log si el snapshot/version ya lo cubre.

---

## 60. Integracion con IA

Solicitudes posibles:

- "Mejora el contraste del tema oscuro".
- "Haz los botones menos redondeados".
- "Usa una tipografia mas formal".
- "Prepara un estilo compacto para una app administrativa".

La IA produce un parche estructurado contra revision base:

```json
{
  "base_revision": 4,
  "patch": {
    "dark.on_surface": "#F8FAFC",
    "shape.button_radius": 6
  },
  "reasoning_summary": "Mejora contraste y reduce redondeo",
  "diagnostics": []
}
```

Mostrar diferencias y exigir confirmacion. La IA no entrega CSS ni Dart.

---

## 61. Seguridad

- JWT obligatorio.
- Membresia en lectura.
- Permiso de edicion en mutaciones.
- IDOR prevenido por proyecto.
- JSON con limites.
- Nombres de preset sanitizados.
- Sin CSS, HTML, URL o scripts arbitrarios.
- Fuentes solo del catalogo.
- Sin carga de archivos de fuente desde UI inicialmente.
- Sin secrets en config JSON.
- Rate limit razonable para propuestas IA.
- ETag para concurrencia.

---

## 62. Rendimiento

- Preview re-renderiza solo secciones afectadas.
- Debounce visual corto para inputs de texto/color, sin retrasar sliders excesivamente.
- No guardar por cada movimiento.
- Memoizar modelo derivado costoso.
- Cargar assets de fuente bajo demanda y cachearlos.
- No recompilar Flutter para cada cambio.
- Compilar `ui_manifest` solo cuando cambia la fuente funcional.
- Virtualizar listas de presets solo si volumen real lo justifica.

---

## 63. Manejo de errores

- Tema no encontrado: usar default sin fingir fila persistida.
- Version futura: bloquear edicion y explicar.
- Preset invalido: no aplicar.
- Manifest desactualizado: solicitar regenerar preflight.
- Manifest invalido: mostrar diagnostico y no inventar preview.
- Fuente ausente: fallback visible y error de fidelidad.
- Conflicto 409: conservar borrador.
- WebSocket caido: REST sigue guardando; reconexion recupera.
- Generacion falla: tema persistido permanece.

---

## 64. Observabilidad

Registrar:

- `project_id`.
- `theme_revision`.
- `schema_version`.
- `theme_hash`.
- Secciones cambiadas.
- Preset usado.
- Duracion de normalizacion.
- Cantidad de diagnosticos.
- Manifest version/hash.
- Correlation ID.

Metricas:

- Guardados exitosos/fallidos.
- Conflictos de revision.
- Presets aplicados.
- Fallos de contraste.
- Manifiestos no soportados.
- Divergencias de fidelidad detectadas.

---

## 65. Pruebas unitarias backend

Cubrir:

- Default v2.
- Adaptador v1 -> v2.
- Version futura rechazada.
- Colores validos/invalidos.
- Normalizacion mayuscula.
- Radios fuera de rango.
- Enum invalido.
- Fuente no catalogada.
- Peso no disponible.
- Tema claro incompleto.
- Tema oscuro incompleto.
- Contraste.
- Hash estable.
- PUT idempotente.
- Revision incrementa.
- Revision obsoleta produce 409.
- Preset unico.
- Aplicar preset copia config.
- Eliminar preset conserva tema.
- Permisos.
- Evento posterior al commit.

---

## 66. Pruebas de conformidad

Ejecutar los mismos fixtures contra:

- Normalizador Python.
- Normalizador TypeScript.
- Adaptador Flutter/generador.

Para cada fixture comparar JSON canonico:

- Defaults.
- V1 adaptado.
- Valores limites.
- Invalidos corregibles.
- Invalidos bloqueantes.
- Claro/oscuro.
- Cada variante de componente.

Si difieren, falla la prueba. Esta es la defensa principal contra normalizadores divergentes.

---

## 67. Pruebas React

Cubrir:

- Carga de tema persistido.
- Borrador independiente.
- Aplicar preset no guarda.
- Guardar envia revision.
- Cancelar restaura.
- Conflicto conserva borrador.
- Cambio light/dark.
- Selector de viewport.
- Modulos reales del manifest.
- Lista real.
- Detalle real.
- Formulario real.
- Accion en placement correcto.
- Estado loading/empty/error.
- Diagnostico de contraste.
- Fuente catalogada.
- Textos largos.
- Usuario lector no edita.

---

## 68. Pruebas Playwright

Agregar escenarios en viewports definidos:

- Editor completo sin solapamientos.
- Preview movil compacto.
- Preview movil comun.
- Tablet.
- Escritorio.
- Tema claro.
- Tema oscuro.
- Escala de texto aumentada.
- Labels largos.
- Selector de entidad largo.
- Dialogo de confirmacion.
- Menu de navegacion.

Tomar screenshots estables con datos/fuentes locales. Comprobar ademas bounding boxes para detectar elementos fuera del contenedor, no solo comparar imagen.

---

## 69. Pruebas Flutter de tema

Generar/ejecutar:

- ThemeData claro contiene tokens.
- ThemeData oscuro contiene tokens.
- ThemeMode coincide.
- TextTheme usa familia/pesos.
- Botones usan variante/radio.
- Inputs usan variante/radio.
- Cards usan receta.
- Navegacion usa estilo.
- Dialogos usan tema.
- Fuente esta declarada en `pubspec.yaml`.
- Assets existen.

No validar solo cadenas del archivo; construir widgets cuando sea posible.

---

## 70. Golden tests Flutter

Fixtures minimos:

- Lista clara y oscura.
- Detalle.
- Formulario con todos los controles.
- Selector de entidad con label largo.
- Loading/empty/error.
- Confirmacion.
- Navegacion.

Fijar:

- Tamano.
- DPR.
- Fuente local.
- Locale.
- Datos.
- Animaciones desactivadas.

Actualizar golden solo tras revision consciente. No aceptar cambios masivos automaticamente.

---

## 71. Comparacion preview-Flutter

Construir una matriz de trazabilidad:

| Propiedad | Contrato | Preview React | Flutter | Prueba |
| --- | --- | --- | --- | --- |
| light.primary | V2 | CSS token | ColorScheme.primary | conformidad/golden |
| button_style | V2 | PreviewButton | PrimaryActionButton | component test |
| form.date | ui_manifest | DatePreview | showDatePicker | contract test |

Para componentes principales, comparar capturas de referencia con tolerancia documentada. Complementar con comparacion estructural; una similitud visual no prueba que ruta/accion sea correcta.

---

## 72. Prueba integral de Inscripcion

Usar fixture de Fase 5:

- Estudiante.
- Curso.
- Inscripcion.
- Accion `Inscribir estudiante`.
- Selectores de Estudiante y Curso.
- Fecha.
- Confirmacion opcional.

Verificar en preview y Flutter:

- Mismos campos y orden.
- Mismas etiquetas.
- Mismos tipos de control.
- Mismos botones.
- Mismos tokens.
- Modo claro/oscuro.
- Texto largo sin overflow.
- Densidad compacta y comfortable.
- Preset aplicado llega al ZIP.

---

## 73. Prueba de persistencia

1. Abrir proyecto sin tema.
2. Recibir default v2.
3. Editar y guardar.
4. Recargar navegador.
5. Ver mismos valores.
6. Abrir segundo usuario.
7. Ver tema confirmado.
8. Modificar desde uno.
9. Recibir evento en otro.
10. Generar Flutter.
11. Ver hash/tema en manifiesto.
12. Inspeccionar `app_theme.dart` y assets.

---

## 74. Prueba de snapshots

En esta fase verificar serializacion:

- `ProjectSnapshotV2.flutter_theme` incluye config, version y revision relevante.
- Snapshot antiguo sin tema usa default.
- Restauracion simulada valida schema.
- El snapshot no incluye la biblioteca de presets personalizados; incluye unicamente el tema activo normalizado. Restaurar una version no crea, modifica ni elimina presets.

La restauracion operativa completa y backup previo se prueba en Fase 7.

---

## 75. Regresion

- Generacion Flutter sin tema explicito conserva default.
- Tema v1 sigue generando.
- Presets iniciales conservan intencion visual.
- Boton `outline` usa widget correcto.
- Date picker sigue generado.
- Switch sigue generado.
- Dropdown de association class sigue generado.
- Generacion coordinada de Fase 5 sigue pasando.
- Editor UML no cambia.
- Tema global de CASE no se mezcla con Flutter.
- Modo oscuro de CASE no fuerza preview oscuro.

---

## 76. Criterios de aceptacion funcional

### Tema persistente

Guardar, recargar y generar conserva estilo.

### Claro y oscuro

Ambos modos tienen paletas completas y aparecen en ZIP.

### Preview real

Seleccionar Inscripcion muestra campos/acciones reales, no Cliente fijo.

### Preset

Aplicar cambia borrador; guardar persiste; eliminar preset no borra tema.

### Conflicto

Dos editores no se pisan silenciosamente.

### Config invalida

Se rechaza o normaliza con diagnostico preciso.

### Fidelidad

Cada propiedad soportada tiene efecto en preview y Flutter.

### Overflow

No hay elementos fuera de pantalla en fixtures criticos.

---

## 77. Criterios de aceptacion tecnicos

- Contrato v2 tipado en Python y TypeScript.
- Fixtures de conformidad pasan.
- V1 se adapta.
- Persistencia usa revision.
- Eventos ocurren despues de commit.
- `ui_manifest` es la fuente funcional.
- No hay contenido ficticio como flujo principal.
- Fuentes declaradas existen.
- Flutter analyze/test/build pasa.
- Golden tests pasan.
- React tests pasan.
- Playwright pasa en viewports.
- Contraste se evalua.
- No hay overflow.
- Hash de tema coincide en preview/generacion.
- No hay secretos ni URLs remotas inesperadas.

---

## 78. Compatibilidad

- `FlutterThemeConfig` v1 se sigue aceptando.
- `FrontendGenerationRequest.theme_config` puede aceptar v1/v2 durante transicion.
- Respuestas nuevas incluyen version sin quitar campos de golpe si clientes actuales dependen de ellos.
- Generaciones antiguas mantienen su manifiesto historico.
- Tema por proyecto es default, pero override anterior sigue documentado durante migracion.
- Presets locales actuales migran a presets del sistema.

Definir fecha/condicion de retiro de v1, no eliminarlo en esta fase.

---

## 79. Orden obligatorio de implementacion

1. Ejecutar regresion del preview/tema actual.
2. Auditar persistencia de Fase 1.
3. Definir JSON Schema v2 y defaults.
4. Definir catalogos de fuentes/componentes.
5. Crear fixtures de conformidad.
6. Implementar adaptador v1 -> v2.
7. Implementar normalizador backend.
8. Implementar normalizador frontend conforme.
9. Completar modelo/migracion de tema y presets.
10. Implementar API, ETag y permisos.
11. Integrar auditoria/WebSocket.
12. Extender `ui_manifest` si falta informacion visual.
13. Extraer editor React de `GenerationPage`.
14. Implementar paneles de estilo.
15. Implementar preview por manifiesto.
16. Implementar pantallas/estados.
17. Extender ThemeData Flutter.
18. Incluir fuentes/assets/licencias.
19. Integrar tema con todos los widgets de Fase 5.
20. Generar `ui_manifest` y hash efectivos.
21. Agregar pruebas backend/frontend.
22. Agregar Playwright.
23. Agregar golden tests.
24. Ejecutar fixture Inscripcion.
25. Ejecutar build real.
26. Documentar resultados.

---

## 80. Comandos de verificacion CASE

```powershell
cd backend
pytest tests/test_flutter_theme.py -q
pytest tests/test_phase9_flutter_generator.py -q
pytest tests/test_coordinated_generation.py -q
pytest
```

```powershell
cd frontend
npm run test -- --run
npm run build
npx playwright test
```

Adaptar nombres de pruebas a los archivos reales creados.

---

## 81. Comandos de verificacion Flutter generado

```powershell
flutter pub get
dart format --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build web
```

Si existen golden tests separados:

```powershell
flutter test test/goldens
```

No actualizar goldens como parte automatica de la verificacion normal.

---

## 82. Documentacion a producir

Crear:

```text
docs/segundo_parcial/fase6/
  00_indice_fase6.md
  01_contrato_tema_v2.md
  02_normalizacion_compatibilidad.md
  03_editor_visual.md
  04_preview_ui_manifest.md
  05_integracion_flutter.md
  06_presets_fuentes_assets.md
  07_accesibilidad_responsive.md
  08_pruebas_fidelidad.md
  09_guia_usuario_editor_estilos.md
  10_resumen_fase6.md
  11_acta_cierre_fase6.md
  diagramas/
    flujo_edicion_tema.mmd
    fuentes_contrato_preview_flutter.mmd
    sincronizacion_colaborativa_tema.mmd
```

Actualizar `docs/segundo_parcial/previsualizar_frontend` o referenciarlo como antecedente; no mantener documentacion contradictoria.

---

## 83. Entregables

- Contrato de tema v2.
- Defaults y fixtures compartidos.
- Adaptador v1.
- Normalizadores conformes.
- Persistencia de tema con revision.
- Presets personalizados.
- API completa.
- Editor visual modular.
- Preview por `ui_manifest`.
- Claro/oscuro.
- Fuentes realmente incluidas.
- Component recipes.
- ThemeData Flutter completo.
- Integracion con generacion coordinada.
- Integracion con snapshots.
- Pruebas unitarias y visuales.
- Documentacion.

---

## 84. Prohibiciones

- No convertir esto en constructor libre de pantallas.
- No crear contenido funcional ficticio si existe manifest.
- No mostrar controles que Flutter no genera.
- No aceptar CSS/Dart libre.
- No descargar fuentes en runtime.
- No declarar fuentes ausentes.
- No duplicar defaults sin pruebas de conformidad.
- No guardar por cada movimiento del slider.
- No sobrescribir conflictos.
- No confundir tema CASE con tema Flutter.
- No incrustar colores en pantallas generadas.
- No usar unicamente screenshots como prueba contractual.
- No ocultar overflows.
- No actualizar goldens automaticamente.
- No afirmar pixel-perfect entre React y Flutter sin tolerancia.
- No eliminar compatibilidad v1 abruptamente.
- No excluir tema de snapshots.

---

## 85. Lista final de comprobacion

- [ ] Tema v2 esta definido.
- [ ] V1 se adapta correctamente.
- [ ] Defaults son unicos y versionados.
- [ ] Python/TypeScript/Flutter son conformes.
- [ ] Claro y oscuro funcionan.
- [ ] Contraste se valida.
- [ ] Fuente visible esta incluida.
- [ ] Pesos existen.
- [ ] Botones coinciden.
- [ ] Inputs coinciden.
- [ ] Cards coinciden.
- [ ] Navegacion coincide.
- [ ] Dialogos coinciden.
- [ ] Densidad coincide.
- [ ] Radios coinciden.
- [ ] Preview usa manifest real.
- [ ] Lista real se previsualiza.
- [ ] Detalle real se previsualiza.
- [ ] Formulario real se previsualiza.
- [ ] Acciones reales aparecen en placement correcto.
- [ ] Estados visuales existen.
- [ ] Presets de sistema funcionan.
- [ ] Presets personalizados persisten.
- [ ] Aplicar preset no guarda solo.
- [ ] ETag evita sobrescritura.
- [ ] WebSocket sincroniza.
- [ ] Snapshot incluye tema.
- [ ] Generador usa tema efectivo.
- [ ] Manifest guarda hash/version.
- [ ] Textos largos no desbordan.
- [ ] Viewports pasan.
- [ ] Escala de texto pasa.
- [ ] Pruebas React pasan.
- [ ] Playwright pasa.
- [ ] Flutter analyze/test/build pasa.
- [ ] Golden tests pasan.
- [ ] Regresion anterior pasa.

---

## 86. Informe final requerido

Al concluir, reportar:

1. Contrato final de tema.
2. Estrategia v1 -> v2.
3. Catalogos soportados.
4. Persistencia y presets.
5. Arquitectura del editor.
6. Arquitectura del preview.
7. Integracion con `ui_manifest`.
8. Integracion con Flutter.
9. Estrategia de fuentes.
10. Contraste y accesibilidad.
11. Sincronizacion colaborativa.
12. Integracion con snapshots.
13. Pruebas de conformidad.
14. Pruebas Playwright.
15. Golden tests Flutter.
16. Resultado de analyze/test/build.
17. Divergencias conocidas y tolerancias.
18. Contratos entregados a Fase 7.

---

## 87. Resultado final esperado

CASE Inteligente debe ofrecer un editor de estilos preciso y acotado. El usuario personaliza la apariencia de la aplicacion Flutter mediante opciones soportadas, observa pantallas y acciones derivadas de su propio diagrama y guarda una configuracion compartida por proyecto.

La previsualizacion no es una maqueta decorativa: representa el mismo manifiesto funcional, los mismos tokens y las mismas recetas de componentes que usa el generador. Lista, detalle, formularios, filtros, selectores, botones, dialogos y estados deben existir en ambos lados.

El proyecto Flutter descargado debe conservar tema claro/oscuro, tipografia, colores, radios, densidad y estilos sin depender de recursos remotos. Las pruebas de conformidad, viewport y golden deben detectar cuando preview y ZIP divergen. Al finalizar, la configuracion queda lista para formar parte segura del versionado, bitacora y restauracion de la Fase 7.
