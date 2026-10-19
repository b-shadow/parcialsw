import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Menu, Moon, MoreVertical, Plus, RotateCcw, Save, Sun, Trash2 } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { ProjectSocketClient } from "../../../core/websocket/projectSocket";
import { generationService } from "../services/generationService";
import { firstPreviewScreen, localThemeDiagnostics, resolveColorModeTokens, resolveDensityRecipe, sampleValue } from "../theme/themeContract";
import type { FlutterThemeConfig, FlutterThemePreset, ThemePalette, UiManifest, UiManifestScreen } from "../types/generation";

type Props = { projectId: string; transformationId?: string; value: FlutterThemeConfig; onChange: (theme: FlutterThemeConfig) => void };
type PreviewState = "content" | "loading" | "empty" | "error" | "offline" | "unauthorized" | "success";

const selectClass = "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20";

export function FlutterStyleWorkspace({ projectId, transformationId, value, onChange }: Props) {
  const [saved, setSaved] = useState(value);
  const [revision, setRevision] = useState(0);
  const [presets, setPresets] = useState<FlutterThemePreset[]>([]);
  const [manifest, setManifest] = useState<UiManifest | null>(null);
  const [mode, setMode] = useState<"light" | "dark">("light");
  const [screen, setScreen] = useState<UiManifestScreen | null>(null);
  const [previewState, setPreviewState] = useState<PreviewState>("content");
  const [textScale, setTextScale] = useState("100");
  const [viewport, setViewport] = useState<"mobile" | "tablet" | "desktop">("mobile");
  const [message, setMessage] = useState("");
  const diagnostics = useMemo(() => localThemeDiagnostics(value), [value]);
  const dirty = JSON.stringify(saved) !== JSON.stringify(value);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([generationService.getTheme(projectId), generationService.presets(projectId)])
      .then(([theme, items]) => { setSaved(theme.theme); onChange(theme.theme); setRevision(theme.revision); setPresets(items); })
      .catch(() => setMessage("No se pudo cargar el estilo guardado."));
  }, [projectId]);

  useEffect(() => {
    if (!transformationId) { setManifest(null); setScreen(null); return; }
    generationService.uiManifest(transformationId).then((result) => { setManifest(result); setScreen(firstPreviewScreen(result)); })
      .catch(() => setMessage("No se pudo cargar el manifiesto real del preview."));
  }, [transformationId]);

  useEffect(() => {
    if (!projectId) return;
    const client = new ProjectSocketClient({ projectId, getProjectSequence: () => 0,
      getConversationSequence: () => 0, onStatus: () => undefined,
      onEvent: (event) => {
        if (event.type !== "FLUTTER_THEME_UPDATED") return;
        if (dirty) { setMessage("Otro colaborador guardo el tema. Su borrador se conserva; compare o cancele antes de guardar."); return; }
        generationService.getTheme(projectId).then((result) => { setSaved(result.theme); onChange(result.theme); setRevision(result.revision); });
      } });
    client.connect();
    return () => client.close();
  }, [projectId, dirty]);

  function palettePatch(patch: Partial<ThemePalette>) { onChange({ ...value, [mode]: { ...value[mode], ...patch } }); }
  async function save() {
    if (diagnostics.some((item) => item.severity === "error")) { setMessage("Corrija los contrastes antes de guardar."); return; }
    try {
      const result = await generationService.saveTheme(projectId, value, revision);
      setSaved(result.theme); onChange(result.theme); setRevision(result.revision); setMessage(`Estilo guardado, revision ${result.revision}.`);
    } catch { setMessage("El estilo cambio en otra sesion o no supero la validacion. Recargue antes de sobrescribir."); }
  }
  async function createPreset() {
    const name = window.prompt("Nombre del preset");
    if (!name) return;
    try { const preset = await generationService.createPreset(projectId, name, value); setPresets((items) => [...items, preset]); }
    catch { setMessage("No se pudo guardar el preset."); }
  }
  const palette = resolveColorModeTokens(value, mode);
  const density = resolveDensityRecipe(value.components.density);
  const module = manifest?.modules.find((item) => item.screens.some((itemScreen) => itemScreen.id === screen?.id)) ?? manifest?.modules[0];
  const moduleCount = manifest?.modules.length ?? 0;
  const requestedNavigation = value.components.navigation_style === "automatic"
    ? 2 <= moduleCount && moduleCount <= 4 ? "bottom_bar" : "navigation_drawer"
    : value.components.navigation_style;
  const navigation = requestedNavigation === "bottom_bar" && moduleCount < 2
    ? "navigation_drawer"
    : requestedNavigation;

  return <section className="overflow-hidden rounded-md border border-slate-200 bg-white" aria-label="Editor de estilos Flutter" data-testid="flutter-style-editor">
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
      <div><h2 className="font-semibold">Estilo y previsualizacion Flutter</h2><p className="text-xs text-slate-500">Revision {revision}{dirty ? " · Cambios sin guardar" : " · Guardado"}</p></div>
      <div className="flex flex-wrap gap-2">
        <Button icon={<RotateCcw size={16} />} onClick={() => onChange(saved)} variant="ghost">Cancelar</Button>
        <Button icon={<Save size={16} />} disabled={!projectId || !dirty || diagnostics.length > 0} onClick={save}>Guardar estilo</Button>
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
          <Select label="Modo predeterminado" value={value.mode} options={["system", "light", "dark"]} onChange={(themeMode) => onChange({ ...value, mode: themeMode as FlutterThemeConfig["mode"] })}/>
          <label className="grid gap-1 text-xs font-medium">Fuente incluida<input className={selectClass} readOnly value="Sistema"/></label>
          <Select label="Escala tipografica" value={value.typography.scale} options={["compact", "normal", "large"]} onChange={(scale) => onChange({ ...value, typography: { ...value.typography, scale: scale as FlutterThemeConfig["typography"]["scale"] } })}/>
          <Select label="Peso base" value={value.typography.weight} options={["regular", "medium"]} onChange={(weight) => onChange({ ...value, typography: { ...value.typography, weight: weight as "regular" | "medium" } })}/>
          <Select label="Boton" value={value.components.button_style} options={["filled", "outline", "tonal"]} onChange={(button_style) => onChange({ ...value, components: { ...value.components, button_style: button_style as FlutterThemeConfig["components"]["button_style"] } })}/>
          <Select label="Campo" value={value.components.input_style} options={["outline", "filled"]} onChange={(input_style) => onChange({ ...value, components: { ...value.components, input_style: input_style as "outline" | "filled" } })}/>
          <Select label="Card" value={value.components.card_style} options={["flat", "outlined", "elevated"]} onChange={(card_style) => onChange({ ...value, components: { ...value.components, card_style: card_style as "flat" | "outlined" | "elevated" } })}/>
          <Select label="Navegacion" value={value.components.navigation_style} options={["automatic", "bottom_bar", "navigation_drawer"]} onChange={(navigation_style) => onChange({ ...value, components: { ...value.components, navigation_style: navigation_style as FlutterThemeConfig["components"]["navigation_style"] } })}/>
          <Select label="Densidad" value={value.components.density} options={["compact", "normal", "comfortable"]} onChange={(densityValue) => onChange({ ...value, components: { ...value.components, density: densityValue as FlutterThemeConfig["components"]["density"] } })}/>
          {(["button_radius", "input_radius", "card_radius", "dialog_radius"] as const).map((token) => <label className="grid gap-1 text-xs" key={token}>{token.replace("_", " ")}: {value.shape[token]} px<input className="accent-teal-700" min="0" max="24" type="range" value={value.shape[token]} onChange={(event) => onChange({ ...value, shape: { ...value.shape, [token]: Number(event.target.value) } })}/></label>)}
        </div>
        <div><h3 className="text-sm font-semibold">Presets</h3><div className="mt-2 grid gap-2"><Button icon={<Plus size={16}/>} onClick={createPreset} variant="secondary">Guardar preset</Button>{presets.map((preset) => <div className="flex items-center gap-1" key={preset.id}><button className="min-w-0 flex-1 truncate rounded border px-2 py-2 text-left text-xs" onClick={() => onChange(preset.config)}>{preset.name}</button>{preset.kind === "custom" && <button aria-label={`Eliminar ${preset.name}`} className="p-2 text-rose-600" onClick={async () => { await generationService.deletePreset(projectId, preset.id); setPresets((items) => items.filter((item) => item.id !== preset.id)); }}><Trash2 size={16}/></button>}</div>)}</div></div>
      </aside>

      <main className="min-w-0 bg-slate-100 p-4 sm:p-6">
        <div className="mx-auto overflow-hidden border shadow-sm transition-[max-width]" style={{ maxWidth: viewport === "mobile" ? 430 : viewport === "tablet" ? 760 : 980, background: palette.background, color: palette.on_background, borderColor: palette.outline, borderRadius: 18, fontFamily: value.typography.font_family === "system" ? "system-ui" : value.typography.font_family, fontSize: `${Number(textScale) / 100}em` }}>
          <div className="flex min-h-14 items-center justify-between px-4" style={{ background: palette.primary, color: palette.on_primary }}><span className="flex min-w-0 items-center gap-2">{navigation === "navigation_drawer" && <Menu className="shrink-0" size={18}/>}<strong className="truncate">{module?.label ?? "Seleccione un diagrama"}</strong></span><MoreVertical className="shrink-0" size={18}/></div>
          <div className="flex min-h-[520px]">
            {navigation === "navigation_drawer" && <nav aria-label="Navegacion lateral del preview" className="w-[38%] shrink-0 border-r p-2" style={{ background: palette.surface, borderColor: palette.outline }}>{manifest?.modules.map((item) => <button className="mb-1 block w-full truncate rounded px-2 py-2 text-left text-xs" key={item.id} style={item.id === module?.id ? { background: palette.secondary, color: palette.on_secondary } : undefined}>{item.label}</button>)}</nav>}
            <div className="grid min-w-0 flex-1 content-start" style={{ gap: density.gap, padding: density.padding }}>{renderPreview(screen, previewState, palette, value, density.height)}</div>
          </div>
          {navigation === "bottom_bar" && <nav aria-label="Navegacion inferior del preview" className="grid min-h-16 border-t" style={{ gridTemplateColumns: `repeat(${Math.max(1, manifest?.modules.length ?? 1)}, minmax(0, 1fr))`, background: palette.surface, color: palette.on_surface, borderColor: palette.outline }}>{manifest?.modules.map((item) => <button className="min-w-0 px-2 py-2 text-xs" key={item.id} style={item.id === module?.id ? { color: palette.primary } : undefined}><span className="mx-auto mb-1 block h-2 w-2 rounded-full" style={{ background: item.id === module?.id ? palette.primary : palette.outline }}/><span className="block truncate">{item.label}</span></button>)}</nav>}
        </div>
      </main>

      <aside className="grid content-start gap-4 border-t border-slate-200 p-4 xl:border-l xl:border-t-0">
        <Select label="Modulo" value={module?.id ?? ""} options={manifest?.modules.map((item) => item.id) ?? []} labels={Object.fromEntries(manifest?.modules.map((item) => [item.id, item.label]) ?? [])} onChange={(id) => setScreen(manifest?.modules.find((item) => item.id === id)?.screens[0] ?? null)}/>
        <Select label="Pantalla" value={screen?.id ?? ""} options={module?.screens.map((item) => item.id) ?? []} labels={Object.fromEntries(module?.screens.map((item) => [item.id, `${item.kind}: ${item.title}`]) ?? [])} onChange={(id) => setScreen(module?.screens.find((item) => item.id === id) ?? null)}/>
        <Select label="Estado" value={previewState} options={["content", "loading", "empty", "error", "offline", "unauthorized", "success"]} onChange={(state) => setPreviewState(state as PreviewState)}/>
        <Select label="Viewport" value={viewport} options={["mobile", "tablet", "desktop"]} onChange={(item) => setViewport(item as typeof viewport)}/>
        <Select label="Escala de texto" value={textScale} options={["100", "130", "160"]} labels={{ "100": "100%", "130": "130%", "160": "160%" }} onChange={setTextScale}/>
        <div><h3 className="text-sm font-semibold">Diagnosticos</h3>{diagnostics.length === 0 ? <p className="mt-2 text-xs text-emerald-700">Contraste valido.</p> : <ul className="mt-2 grid gap-2">{diagnostics.map((item) => <li className="flex gap-2 text-xs text-rose-700" key={item.path}><AlertTriangle className="shrink-0" size={15}/><span>{item.path}: {item.message}</span></li>)}</ul>}</div>
        {manifest && <p className="break-all text-[11px] text-slate-500">Modelo {manifest.source_hash.slice(0, 12)} · {manifest.modules.length} modulos</p>}
      </aside>
    </div>
  </section>;
}

function Select({ label, value, options, labels = {}, onChange }: { label: string; value: string; options: string[]; labels?: Record<string, string>; onChange: (value: string) => void }) {
  return <label className="grid gap-1 text-xs font-medium">{label}<select className={selectClass} value={value} onChange={(event) => onChange(event.target.value)}>{options.length === 0 && <option value="">No disponible</option>}{options.map((option) => <option key={option} value={option}>{labels[option] ?? option}</option>)}</select></label>;
}

function renderPreview(screen: UiManifestScreen | null, state: PreviewState, palette: ThemePalette, theme: FlutterThemeConfig, height: number) {
  if (state !== "content") return <div className="grid min-h-72 place-items-center text-center"><div><strong>{({ loading: "Cargando", empty: "Sin registros", error: "No se pudo cargar", offline: "Sin conexion", unauthorized: "Acceso restringido", success: "Operacion completada" } as Record<string,string>)[state]}</strong><p className="mt-2 text-sm opacity-70">Estado disponible tambien en la aplicacion generada.</p></div></div>;
  if (!screen) return <div className="grid min-h-72 place-items-center text-sm">Transforme un diagrama para previsualizarlo.</div>;
  const cardStyle = { background: palette.surface, color: palette.on_surface, borderColor: palette.outline, borderRadius: theme.shape.card_radius, boxShadow: theme.components.card_style === "elevated" ? "0 2px 8px #0002" : "none", borderWidth: theme.components.card_style === "outlined" ? 1 : 0 };
  const buttonStyle = theme.components.button_style === "outline" ? { background: "transparent", color: palette.primary, border: `1px solid ${palette.primary}` } : { background: theme.components.button_style === "tonal" ? palette.secondary : palette.primary, color: theme.components.button_style === "tonal" ? palette.on_secondary : palette.on_primary, border: "1px solid transparent" };
  if (screen.kind === "list") return <>{[1,2,3].map((index) => <div className="border p-3" key={index} style={cardStyle}><strong className="block truncate">{screen.title} {index}</strong><p className="mt-1 truncate text-sm opacity-75">{screen.fields.slice(0,2).map((field) => `${field.label}: ${sampleValue(field)}`).join(" · ") || "Sin campos visibles"}</p></div>)}<button className="ml-auto mt-2 h-12 w-12 rounded-full text-xl" style={{ background: palette.primary, color: palette.on_primary }}>+</button></>;
  return <><h3 className="font-semibold">{screen.title}</h3>{screen.fields.map((field) => screen.kind === "detail" ? <div className="border-b py-2" key={field.id}><span className="block text-xs opacity-65">{field.label}</span><span className="break-words text-sm">{sampleValue(field)}</span></div> : <label className="grid gap-1 text-xs" key={field.id}>{theme.components.show_field_labels && field.label}<span className="flex items-center border px-3 text-sm" style={{ minHeight: height, borderRadius: theme.shape.input_radius, borderColor: palette.outline, background: theme.components.input_style === "filled" ? palette.surface : "transparent" }}>{sampleValue(field)}</span></label>)}{screen.kind !== "detail" && <button className="mt-2 min-h-12 px-4 font-semibold" style={{ ...buttonStyle, borderRadius: theme.shape.button_radius }}>Guardar</button>}{screen.actions.map((action) => <button className="min-h-11 px-3 text-sm" key={action.id} style={{ ...buttonStyle, borderRadius: theme.shape.button_radius }}>{action.label}</button>)}</>;
}
