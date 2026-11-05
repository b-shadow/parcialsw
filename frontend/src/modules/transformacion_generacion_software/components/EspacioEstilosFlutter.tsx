import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Menu, Moon, MoreVertical, Plus, RotateCcw, Save, Sun, Trash2 } from "lucide-react";

import { Boton } from "../../../shared/components/Boton";
import { ClienteSocketProyecto } from "../../../core/websocket/socketProyecto";
import { servicioGeneracion } from "../services/servicioGeneracion";
import { primeraPantallaVistaPrevia, diagnosticosTemaLocal, resolverTokensModoColor, resolverRecetaDensidad, valorEjemplo } from "../theme/contratoTema";
import type { ConfiguracionTemaFlutter, TemaFlutterPredefinido, PaletaTema, ManifiestoUI, PantallaManifiestoUI } from "../types/generacion";

type Props = { projectId: string; transformationId?: string; value: ConfiguracionTemaFlutter; onChange: (theme: ConfiguracionTemaFlutter) => void };
type PreviewState = "content" | "loading" | "empty" | "error" | "offline" | "unauthorized" | "success";

const selectClass = "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20";

export function EspacioEstilosFlutter({ projectId, transformationId, value, onChange }: Props) {
  const [saved, setSaved] = useState(value);
  const [revision, setRevision] = useState(0);
  const [presets, setPresets] = useState<TemaFlutterPredefinido[]>([]);
  const [manifest, setManifest] = useState<ManifiestoUI | null>(null);
  const [mode, setMode] = useState<"light" | "dark">("light");
  const [screen, setScreen] = useState<PantallaManifiestoUI | null>(null);
  const [previewState, setPreviewState] = useState<PreviewState>("content");
  const [textScale, setTextScale] = useState("100");
  const [viewport, setViewport] = useState<"mobile" | "tablet" | "desktop">("mobile");
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [message, setMessage] = useState("");
  const diagnostics = useMemo(() => diagnosticosTemaLocal(value), [value]);
  const dirty = JSON.stringify(saved) !== JSON.stringify(value);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([servicioGeneracion.getTheme(projectId), servicioGeneracion.presets(projectId)])
      .then(([theme, items]) => { setSaved(theme.theme); onChange(theme.theme); setRevision(theme.revision); setPresets(items); })
      .catch(() => setMessage("No se pudo cargar el estilo guardado."));
  }, [projectId]);

  useEffect(() => {
    if (!transformationId) { setManifest(null); setScreen(null); return; }
    let active = true;
    servicioGeneracion.uiManifest(transformationId).then((result) => {
      if (!active) return;
      setManifest(result);
      setScreen(primeraPantallaVistaPrevia(result));
      setPreviewState("content");
    }).catch(() => { if (active) { setManifest(null); setScreen(null); setMessage("No se pudo cargar el manifiesto real del preview."); } });
    return () => { active = false; };
  }, [transformationId]);

  useEffect(() => {
    if (value.mode === "light" || value.mode === "dark") setMode(value.mode);
    else if (typeof window.matchMedia === "function") setMode(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }, [value.mode]);

  useEffect(() => {
    if (!projectId) return;
    const client = new ClienteSocketProyecto({ projectId, getProjectSequence: () => 0,
      getConversationSequence: () => 0, onStatus: () => undefined,
      onEvent: (event) => {
        if (event.type !== "FLUTTER_THEME_UPDATED") return;
        if (dirty) { setMessage("Otro colaborador guardo el tema. Su borrador se conserva; compare o cancele antes de guardar."); return; }
        servicioGeneracion.getTheme(projectId).then((result) => { setSaved(result.theme); onChange(result.theme); setRevision(result.revision); });
      } });
    client.connect();
    return () => client.close();
  }, [projectId, dirty]);

  function palettePatch(patch: Partial<PaletaTema>) { onChange({ ...value, [mode]: { ...value[mode], ...patch } }); }
  async function save() {
    if (diagnostics.some((item) => item.severity === "error")) { setMessage("Corrija los contrastes antes de guardar."); return; }
    try {
      const result = await servicioGeneracion.saveTheme(projectId, value, revision);
      setSaved(result.theme); onChange(result.theme); setRevision(result.revision); setMessage(`Estilo guardado, revision ${result.revision}.`);
    } catch { setMessage("El estilo cambio en otra sesion o no supero la validacion. Recargue antes de sobrescribir."); }
  }
  async function createPreset() {
    const name = window.prompt("Nombre del preset");
    if (!name) return;
    try { const preset = await servicioGeneracion.createPreset(projectId, name, value); setPresets((items) => [...items, preset]); }
    catch { setMessage("No se pudo guardar el preset."); }
  }
  const palette = resolverTokensModoColor(value, mode);
  const density = resolverRecetaDensidad(value.components.density);
  const module = manifest?.modules.find((item) => item.screens.some((itemScreen) => itemScreen.id === screen?.id)) ?? manifest?.modules[0];
  const moduleCount = manifest?.modules.length ?? 0;
  const requestedNavigation = value.components.navigation_style === "automatic"
    ? 2 <= moduleCount && moduleCount <= 4 ? "bottom_bar" : "navigation_drawer"
    : value.components.navigation_style;
  const navigation = requestedNavigation === "bottom_bar" && moduleCount < 2
    ? "navigation_drawer"
    : requestedNavigation;
  const typographyScale = value.typography.scale === "compact" ? 0.875 : value.typography.scale === "large" ? 1.2 : 1;
  const previewFontSize = `${Number(textScale) / 100 * typographyScale}em`;
  const selectModule = (id: string) => {
    setScreen(manifest?.modules.find((item) => item.id === id)?.screens[0] ?? null);
    setPreviewState("content");
    setPreviewDialogOpen(false);
  };
  const focusScreen = (kind: PantallaManifiestoUI["kind"]) => {
    const matching = manifest?.modules.flatMap((item) => item.screens).find((item) => item.kind === kind);
    if (matching) { setScreen(matching); setPreviewState("content"); setPreviewDialogOpen(false); }
  };

  return <section className="overflow-hidden rounded-md border border-slate-200 bg-white" aria-label="Editor de estilos Flutter" data-testid="flutter-style-editor">
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
      <div><h2 className="font-semibold">Estilo y previsualizacion Flutter</h2><p className="text-xs text-slate-500">Revision {revision}{dirty ? " · Cambios sin guardar" : " · Guardado"}</p></div>
      <div className="flex flex-wrap gap-2">
        <Boton icon={<RotateCcw size={16} />} onClick={() => onChange(saved)} variant="ghost">Cancelar</Boton>
        <Boton icon={<Save size={16} />} disabled={!projectId || !dirty || diagnostics.length > 0} onClick={save}>Guardar estilo</Boton>
      </div>
    </header>
    {message && <p className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-sm" role="status">{message}</p>}
    <div className="grid min-w-0 xl:grid-cols-[330px_minmax(0,1fr)_250px]">
      <aside className="grid content-start gap-5 border-b border-slate-200 p-4 xl:border-b-0 xl:border-r">
        <div><h3 className="text-sm font-semibold">Paleta</h3><div className="mt-2 grid grid-cols-2 gap-2">
          <button className={`flex h-9 items-center justify-center gap-2 rounded-md border ${mode === "light" ? "border-teal-700 bg-teal-50" : "border-slate-300"}`} onClick={() => setMode("light")}><Sun size={16}/>Claro</button>
          <button className={`flex h-9 items-center justify-center gap-2 rounded-md border ${mode === "dark" ? "border-teal-700 bg-teal-50" : "border-slate-300"}`} onClick={() => setMode("dark")}><Moon size={16}/>Oscuro</button>
        </div></div>
        <div className="grid gap-3">{(["primary", "on_primary", "secondary", "on_secondary", "background", "on_background", "surface", "on_surface", "error", "on_error", "outline"] as const).map((token) => <label className="grid grid-cols-[1fr_42px_96px] items-center gap-2 text-xs" key={token}><span>{token.replace("_", " ")}</span><input aria-label={`Selector ${token}`} className="h-8 w-10" type="color" value={palette[token]} onChange={(event) => palettePatch({ [token]: event.target.value.toUpperCase() })}/><input aria-label={`Hex ${token}`} className="h-8 rounded border px-2 font-mono" value={palette[token]} onChange={(event) => palettePatch({ [token]: event.target.value.toUpperCase() })}/></label>)}</div>
        <div className="grid gap-3"><h3 className="text-sm font-semibold">Componentes</h3>
          <Select label="Modo predeterminado" value={value.mode} options={["system", "light", "dark"]} onChange={(themeMode) => { onChange({ ...value, mode: themeMode as ConfiguracionTemaFlutter["mode"] }); if (themeMode !== "system") setMode(themeMode as "light" | "dark"); else if (typeof window.matchMedia === "function") setMode(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); }}/>
          <label className="grid gap-1 text-xs font-medium">Fuente incluida<input className={selectClass} readOnly value="Sistema"/></label>
          <Select label="Escala tipografica" value={value.typography.scale} options={["compact", "normal", "large"]} onChange={(scale) => onChange({ ...value, typography: { ...value.typography, scale: scale as ConfiguracionTemaFlutter["typography"]["scale"] } })}/>
          <Select label="Peso base" value={value.typography.weight} options={["regular", "medium"]} onChange={(weight) => onChange({ ...value, typography: { ...value.typography, weight: weight as "regular" | "medium" } })}/>
          <Select label="Boton" value={value.components.button_style} options={["filled", "outline", "tonal"]} onChange={(button_style) => onChange({ ...value, components: { ...value.components, button_style: button_style as ConfiguracionTemaFlutter["components"]["button_style"] } })}/>
          <Select label="Campo" value={value.components.input_style} options={["outline", "filled"]} onChange={(input_style) => { onChange({ ...value, components: { ...value.components, input_style: input_style as "outline" | "filled" } }); focusScreen("form"); }}/>
          <Select label="Card" value={value.components.card_style} options={["flat", "outlined", "elevated"]} onChange={(card_style) => { onChange({ ...value, components: { ...value.components, card_style: card_style as "flat" | "outlined" | "elevated" } }); focusScreen("list"); }}/>
          <Select label="Navegacion" value={value.components.navigation_style} options={["automatic", "bottom_bar", "navigation_drawer"]} onChange={(navigation_style) => onChange({ ...value, components: { ...value.components, navigation_style: navigation_style as ConfiguracionTemaFlutter["components"]["navigation_style"] } })}/>
          <Select label="Densidad" value={value.components.density} options={["compact", "normal", "comfortable"]} onChange={(densityValue) => onChange({ ...value, components: { ...value.components, density: densityValue as ConfiguracionTemaFlutter["components"]["density"] } })}/>
          {(["button_radius", "input_radius", "card_radius", "dialog_radius"] as const).map((token) => <label className="grid gap-1 text-xs" key={token}>{token.replace("_", " ")}: {value.shape[token]} px<input className="accent-teal-700" min="0" max="24" type="range" value={value.shape[token]} onChange={(event) => { onChange({ ...value, shape: { ...value.shape, [token]: Number(event.target.value) } }); if (token === "dialog_radius") setPreviewDialogOpen(true); else if (token === "input_radius") focusScreen("form"); else if (token === "card_radius") focusScreen("list"); }}/></label>)}
        </div>
        <div><h3 className="text-sm font-semibold">Presets</h3><div className="mt-2 grid gap-2"><Boton icon={<Plus size={16}/>} onClick={createPreset} variant="secondary">Guardar preset</Boton>{presets.map((preset) => <div className="flex items-center gap-1" key={preset.id}><button className="min-w-0 flex-1 truncate rounded border px-2 py-2 text-left text-xs" onClick={() => onChange(preset.config)}>{preset.name}</button>{preset.kind === "custom" && <button aria-label={`Eliminar ${preset.name}`} className="p-2 text-rose-600" onClick={async () => { await servicioGeneracion.deletePreset(projectId, preset.id); setPresets((items) => items.filter((item) => item.id !== preset.id)); }}><Trash2 size={16}/></button>}</div>)}</div></div>
      </aside>

      <main className="min-w-0 bg-slate-100 p-4 sm:p-6">
        <div aria-label="Previsualización Flutter" className="mx-auto overflow-hidden border shadow-sm transition-[max-width]" data-testid="flutter-preview" data-viewport={viewport} style={{ maxWidth: viewport === "mobile" ? 430 : viewport === "tablet" ? 760 : 980, background: palette.background, color: palette.on_background, borderColor: palette.outline, borderRadius: 18, fontFamily: value.typography.font_family === "system" ? "system-ui" : value.typography.font_family, fontSize: previewFontSize, fontWeight: value.typography.weight === "medium" ? 500 : 400 }}>
          <div className="flex min-h-14 items-center justify-between px-4" style={{ background: palette.primary, color: palette.on_primary }}><span className="flex min-w-0 items-center gap-2">{navigation === "navigation_drawer" && <Menu className="shrink-0" size={18}/>}<strong className="truncate">{module?.label ?? "Seleccione un diagrama"}</strong></span><MoreVertical className="shrink-0" size={18}/></div>
          <div className="flex min-h-[520px]">
            {navigation === "navigation_drawer" && <nav aria-label="Navegacion lateral del preview" className="w-[38%] shrink-0 border-r p-2" style={{ background: palette.surface, borderColor: palette.outline }}>{manifest?.modules.map((item) => <button className="mb-1 block w-full truncate rounded px-2 py-2 text-left text-xs" key={item.id} onClick={() => selectModule(item.id)} style={item.id === module?.id ? { background: palette.secondary, color: palette.on_secondary } : undefined}>{item.label}</button>)}</nav>}
            <div className="relative grid min-w-0 flex-1 content-start" style={{ gap: density.gap, padding: density.padding }}>
              {renderPreview(screen, previewState, palette, value, density.height, () => setPreviewDialogOpen(true))}
              {previewDialogOpen && <div className="absolute inset-0 z-10 grid place-items-center bg-slate-950/50 p-3"><div role="dialog" aria-label="Diálogo de ejemplo" className="w-full max-w-xs border p-4 shadow-lg" style={{ borderRadius: value.shape.dialog_radius, background: palette.surface, color: palette.on_surface, borderColor: palette.outline }}><strong>Confirmar acción</strong><p className="mt-2 text-sm">Así se verá un diálogo de confirmación.</p><div className="mt-4 flex justify-end gap-2"><button className="px-2 py-1 text-sm" onClick={() => setPreviewDialogOpen(false)}>Cancelar</button><button className="px-2 py-1 text-sm" onClick={() => setPreviewDialogOpen(false)} style={{ borderRadius: value.shape.button_radius, background: palette.primary, color: palette.on_primary }}>Confirmar</button></div></div></div>}
            </div>
          </div>
          {navigation === "bottom_bar" && <nav aria-label="Navegacion inferior del preview" className="grid min-h-16 border-t" style={{ gridTemplateColumns: `repeat(${Math.max(1, manifest?.modules.length ?? 1)}, minmax(0, 1fr))`, background: palette.surface, color: palette.on_surface, borderColor: palette.outline }}>{manifest?.modules.map((item) => <button className="min-w-0 px-2 py-2 text-xs" key={item.id} onClick={() => selectModule(item.id)} style={item.id === module?.id ? { color: palette.primary } : undefined}><span className="mx-auto mb-1 block h-2 w-2 rounded-full" style={{ background: item.id === module?.id ? palette.primary : palette.outline }}/><span className="block truncate">{item.label}</span></button>)}</nav>}
        </div>
      </main>

      <aside className="grid content-start gap-4 border-t border-slate-200 p-4 xl:border-l xl:border-t-0">
        <Select label="Modulo" value={module?.id ?? ""} options={manifest?.modules.map((item) => item.id) ?? []} labels={Object.fromEntries(manifest?.modules.map((item) => [item.id, item.label]) ?? [])} onChange={selectModule}/>
        <Select label="Pantalla" value={screen?.id ?? ""} options={module?.screens.map((item) => item.id) ?? []} labels={Object.fromEntries(module?.screens.map((item) => [item.id, `${item.kind}: ${item.title}`]) ?? [])} onChange={(id) => { setScreen(module?.screens.find((item) => item.id === id) ?? null); setPreviewState("content"); setPreviewDialogOpen(false); }}/>
        <Select label="Estado" value={previewState} options={["content", "loading", "empty", "error", "offline", "unauthorized", "success"]} onChange={(state) => setPreviewState(state as PreviewState)}/>
        <Select label="Viewport" value={viewport} options={["mobile", "tablet", "desktop"]} onChange={(item) => setViewport(item as typeof viewport)}/>
        <Select label="Escala de texto" value={textScale} options={["100", "130", "160"]} labels={{ "100": "100%", "130": "130%", "160": "160%" }} onChange={setTextScale}/>
        <button className="h-10 rounded-md border border-slate-300 px-3 text-sm" onClick={() => setPreviewDialogOpen((open) => !open)} type="button">{previewDialogOpen ? "Cerrar diálogo" : "Mostrar diálogo"}</button>
        <div><h3 className="text-sm font-semibold">Diagnosticos</h3>{diagnostics.length === 0 ? <p className="mt-2 text-xs text-emerald-700">Contraste valido.</p> : <ul className="mt-2 grid gap-2">{diagnostics.map((item) => <li className="flex gap-2 text-xs text-rose-700" key={item.path}><AlertTriangle className="shrink-0" size={15}/><span>{item.path}: {item.message}</span></li>)}</ul>}</div>
        {manifest && <p className="break-all text-[11px] text-slate-500">Modelo {manifest.source_hash.slice(0, 12)} · {manifest.modules.length} modulos</p>}
      </aside>
    </div>
  </section>;
}

function Select({ label, value, options, labels = {}, onChange }: { label: string; value: string; options: string[]; labels?: Record<string, string>; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-xs font-medium">{label}<select className={selectClass} value={value} onChange={(event) => onChange(event.target.value)}>{options.length === 0 && <option value="">No disponible</option>}{options.map((option) => <option key={option} value={option}>{labels[option] ?? option}</option>)}</select></label>;
}

function renderPreview(screen: PantallaManifiestoUI | null, state: PreviewState, palette: PaletaTema, theme: ConfiguracionTemaFlutter, height: number, showDialog: () => void) {
  if (state !== "content") {
    const labels: Record<Exclude<PreviewState, "content">, string> = { loading: "Cargando", empty: "Sin registros", error: "No se pudo cargar", offline: "Sin conexión", unauthorized: "Acceso restringido", success: "Operación completada" };
    const alert = state === "error" || state === "offline" || state === "unauthorized";
    return <div className="grid min-h-72 place-items-center text-center" role="status"><div><strong className="inline-block rounded px-3 py-2" style={{ background: alert ? palette.error : palette.primary, color: alert ? palette.on_error : palette.on_primary }}>{labels[state]}</strong><p className="mt-2 text-sm opacity-70">{screen?.title ?? "Vista de la aplicación"}</p></div></div>;
  }
  if (!screen) return <div className="grid min-h-72 place-items-center text-sm">Transforme un diagrama para previsualizarlo.</div>;
  const cardStyle = { background: palette.surface, color: palette.on_surface, borderColor: palette.outline, borderRadius: theme.shape.card_radius, boxShadow: theme.components.card_style === "elevated" ? "0 2px 8px #0002" : "none", borderWidth: theme.components.card_style === "outlined" ? 1 : 0 };
  const buttonStyle = theme.components.button_style === "outline" ? { background: "transparent", color: palette.primary, border: `1px solid ${palette.primary}` } : { background: theme.components.button_style === "tonal" ? palette.secondary : palette.primary, color: theme.components.button_style === "tonal" ? palette.on_secondary : palette.on_primary, border: "1px solid transparent" };
  const actions = screen.actions.map((action) => <button className="min-h-11 px-3 text-sm" key={action.id} onClick={action.confirmation_required ? showDialog : undefined} style={{ ...buttonStyle, borderRadius: theme.shape.button_radius }}>{action.label}</button>);
  if (screen.kind === "list") return <>{[1,2,3].map((index) => <div className="p-3" key={index} style={cardStyle}><strong className="block truncate">{screen.title} {index}</strong><p className="mt-1 truncate text-sm opacity-75">{screen.fields.slice(0,2).map((field) => `${field.label}: ${valorEjemplo(field)}`).join(" · ") || "Sin campos visibles"}</p></div>)}<button className="ml-auto mt-2 h-12 w-12 rounded-full text-xl" style={{ background: palette.primary, color: palette.on_primary, borderRadius: theme.shape.button_radius }}>+</button>{actions}</>;
  return <><h3 className="font-semibold">{screen.title}</h3>{screen.fields.map((field) => screen.kind === "detail" ? <div className="border-b py-2" key={field.id} style={{ borderColor: palette.outline }}><span className="block text-xs opacity-65">{field.label}</span><span className="break-words text-sm">{valorEjemplo(field)}</span></div> : <label className="grid gap-1 text-xs" key={field.id}>{theme.components.show_field_labels && field.label}<span className="flex items-center px-3 text-sm" style={{ minHeight: height, borderRadius: theme.shape.input_radius, border: theme.components.input_style === "filled" ? "none" : `1px solid ${palette.outline}`, borderBottom: theme.components.input_style === "filled" ? `2px solid ${palette.primary}` : undefined, background: theme.components.input_style === "filled" ? palette.surface : "transparent" }}>{valorEjemplo(field)}</span></label>)}{screen.kind === "form" && <button className="mt-2 min-h-12 px-4 font-semibold" style={{ ...buttonStyle, borderRadius: theme.shape.button_radius }}>Guardar</button>}{screen.kind === "filter" && <button className="mt-2 min-h-12 px-4 font-semibold" style={{ ...buttonStyle, borderRadius: theme.shape.button_radius }}>Filtrar</button>}{actions}</>;
}
