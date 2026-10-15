import type { CSSProperties } from "react";
import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, Code2, Database, Download, FolderKanban, Palette, Smartphone } from "lucide-react";

import { Button } from "../../../shared/components/Button";
import { Input } from "../../../shared/components/Input";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { projectService } from "../../gestion_proyectos_colaboracion/services/projectService";
import type { Project } from "../../gestion_proyectos_colaboracion/types/project";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import type { UmlDiagram } from "../../modelado_uml_inteligente/types/uml";
import { generationService } from "../services/generationService";
import type { FlutterThemeConfig, GeneratedBackend, GeneratedFrontend, Transformation } from "../types/generation";

type LoadingKey = "projects" | "diagrams" | "transform" | "backend" | "frontend" | "";

const defaultThemeConfig: FlutterThemeConfig = {
  primary_color: "#0F766E",
  secondary_color: "#14B8A6",
  background_color: "#F8FAFC",
  surface_color: "#FFFFFF",
  button_color: "#0F766E",
  font_family: "Roboto",
  border_radius: 12,
  button_style: "filled",
  density: "normal"
};

const fontOptions = ["Roboto", "Inter", "Poppins", "Montserrat", "Lato", "Nunito", "Merriweather"];

const presetThemes: Array<{ name: string; config: FlutterThemeConfig }> = [
  { name: "Profesional", config: defaultThemeConfig },
  {
    name: "Oscuro",
    config: {
      primary_color: "#2563EB",
      secondary_color: "#38BDF8",
      background_color: "#0F172A",
      surface_color: "#111827",
      button_color: "#2563EB",
      font_family: "Inter",
      border_radius: 14,
      button_style: "filled",
      density: "normal"
    }
  },
  {
    name: "Academico",
    config: {
      primary_color: "#1D4ED8",
      secondary_color: "#F59E0B",
      background_color: "#F8FAFC",
      surface_color: "#FFFFFF",
      button_color: "#1D4ED8",
      font_family: "Merriweather",
      border_radius: 8,
      button_style: "outline",
      density: "comfortable"
    }
  }
];

function hexToRgb(hexColor: string) {
  const value = hexColor.replace("#", "");
  const numeric = Number.parseInt(value, 16);
  return {
    r: (numeric >> 16) & 255,
    g: (numeric >> 8) & 255,
    b: numeric & 255
  };
}

function readableTextColor(hexColor: string) {
  const { r, g, b } = hexToRgb(hexColor);
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  return luminance > 0.62 ? "#0F172A" : "#FFFFFF";
}

function spacingForDensity(density: FlutterThemeConfig["density"]) {
  if (density === "compact") {
    return { gap: 8, padding: 12, fieldHeight: 36 };
  }
  if (density === "comfortable") {
    return { gap: 16, padding: 18, fieldHeight: 46 };
  }
  return { gap: 12, padding: 16, fieldHeight: 40 };
}

function previewButtonStyle(theme: FlutterThemeConfig): CSSProperties {
  if (theme.button_style === "outline") {
    return {
      backgroundColor: "transparent",
      border: `1px solid ${theme.button_color}`,
      borderRadius: theme.border_radius,
      color: theme.button_color
    };
  }
  if (theme.button_style === "tonal") {
    return {
      backgroundColor: `${theme.secondary_color}33`,
      border: `1px solid ${theme.secondary_color}55`,
      borderRadius: theme.border_radius,
      color: theme.button_color
    };
  }
  return {
    backgroundColor: theme.button_color,
    border: `1px solid ${theme.button_color}`,
    borderRadius: theme.border_radius,
    color: readableTextColor(theme.button_color)
  };
}

export function GenerationPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [diagrams, setDiagrams] = useState<UmlDiagram[]>([]);
  const [projectId, setProjectId] = useState("");
  const [diagramId, setDiagramId] = useState("");
  const [name, setName] = useState("AplicacionGenerada");
  const [transformation, setTransformation] = useState<Transformation | null>(null);
  const [backend, setBackend] = useState<GeneratedBackend | null>(null);
  const [frontend, setFrontend] = useState<GeneratedFrontend | null>(null);
  const [apiBaseUrl, setApiBaseUrl] = useState("http://10.0.2.2:8080");
  const [themeConfig, setThemeConfig] = useState<FlutterThemeConfig>(defaultThemeConfig);
  const [loading, setLoading] = useState<LoadingKey>("projects");
  const [error, setError] = useState("");

  const selectedProject = useMemo(() => projects.find((project) => project.id === projectId), [projectId, projects]);
  const selectedDiagram = useMemo(() => diagrams.find((diagram) => diagram.id === diagramId), [diagramId, diagrams]);
  const previewDensity = useMemo(() => spacingForDensity(themeConfig.density), [themeConfig.density]);
  const previewForeground = useMemo(() => readableTextColor(themeConfig.background_color), [themeConfig.background_color]);
  const appBarForeground = useMemo(() => readableTextColor(themeConfig.primary_color), [themeConfig.primary_color]);
  const actionButtonStyle = useMemo(() => previewButtonStyle(themeConfig), [themeConfig]);

  useEffect(() => {
    async function loadProjects() {
      setLoading("projects");
      setError("");
      try {
        const result = await projectService.list();
        setProjects(result);
      } catch {
        setError("No se pudieron cargar los proyectos.");
      } finally {
        setLoading("");
      }
    }

    void loadProjects();
  }, []);

  useEffect(() => {
    async function loadDiagrams() {
      if (!projectId) {
        setDiagrams([]);
        setDiagramId("");
        resetPipeline();
        return;
      }
      setLoading("diagrams");
      setError("");
      setDiagramId("");
      resetPipeline();
      try {
        const result = await umlService.listDiagrams(projectId);
        setDiagrams(result);
      } catch {
        setError("No se pudieron cargar los diagramas del proyecto.");
      } finally {
        setLoading("");
      }
    }

    void loadDiagrams();
  }, [projectId]);

  function resetPipeline() {
    setTransformation(null);
    setBackend(null);
    setFrontend(null);
  }

  function handleDiagramChange(value: string) {
    setDiagramId(value);
    resetPipeline();
  }

  async function handleTransform() {
    if (!diagramId) {
      setError("Seleccione un diagrama UML del proyecto.");
      return;
    }
    setLoading("transform");
    setError("");
    setBackend(null);
    setFrontend(null);
    try {
      const created = await generationService.transform({ diagram_id: diagramId, target_platform: "full_stack" });
      setTransformation(created);
    } catch {
      setError("No se pudo transformar el modelo UML seleccionado.");
    } finally {
      setLoading("");
    }
  }

  async function generateBackend() {
    if (!transformation) {
      return;
    }
    setLoading("backend");
    setError("");
    setFrontend(null);
    try {
      const generated = await generationService.springBoot({
        transformation_id: transformation.id,
        name: `${name}Backend`,
        version_label: "v1"
      });
      setBackend(generated);
    } catch {
      setError("No se pudo generar el backend Spring Boot.");
    } finally {
      setLoading("");
    }
  }

  async function generateFrontend() {
    if (!transformation || !backend) {
      return;
    }
    setLoading("frontend");
    setError("");
    try {
      const generated = await generationService.flutter({
        transformation_id: transformation.id,
        name: `${name}Mobile`,
        version_label: "v1",
        backend_id: backend.id,
        api_base_url: apiBaseUrl.trim() || undefined,
        theme_config: themeConfig
      });
      setFrontend(generated);
    } catch {
      setError("No se pudo generar el frontend Flutter.");
    } finally {
      setLoading("");
    }
  }

  async function downloadBackend() {
    if (!backend) {
      return;
    }
    const blob = await generationService.downloadSpringBoot(backend.id);
    downloadBlob(blob, `${backend.name}.zip`);
  }

  async function downloadFrontend() {
    if (!frontend) {
      return;
    }
    const blob = await generationService.downloadFlutter(frontend.id);
    downloadBlob(blob, `${frontend.name}.zip`);
  }

  function downloadBlob(blob: Blob, fileName: string) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function updateThemeConfig(patch: Partial<FlutterThemeConfig>) {
    setThemeConfig((current) => ({ ...current, ...patch }));
  }

  return (
    <section className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Transformacion y generacion</h1>
        <p className="mt-1 text-sm text-slate-600">Seleccione proyecto y diagrama para generar Spring Boot y Flutter.</p>
      </div>

      {error && <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

      <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
        <Panel className="p-5">
          <div className="grid gap-4">
            <label className="grid gap-1 text-sm font-medium text-slate-700">
              Proyecto
              <select
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                disabled={loading === "projects"}
                value={projectId}
                onChange={(event) => setProjectId(event.target.value)}
              >
                <option value="">Seleccione un proyecto</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm font-medium text-slate-700">
              Diagrama UML
              <select
                className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                disabled={!projectId || loading === "diagrams"}
                value={diagramId}
                onChange={(event) => handleDiagramChange(event.target.value)}
              >
                <option value="">{projectId ? "Seleccione un diagrama" : "Primero seleccione proyecto"}</option>
                {diagrams.map((diagram) => (
                  <option key={diagram.id} value={diagram.id}>
                    {diagram.name}
                  </option>
                ))}
              </select>
            </label>

            <Input label="Nombre base" value={name} onChange={(event) => setName(event.target.value)} />

            <Button disabled={!diagramId || loading === "transform"} icon={<BrainCircuit size={18} aria-hidden="true" />} onClick={handleTransform}>
              {loading === "transform" ? "Transformando" : "Transformar UML"}
            </Button>
          </div>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Panel className="p-5">
            <FolderKanban className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Seleccion</h2>
            <p className="mt-2 text-sm text-slate-600">{selectedProject?.name ?? "Proyecto pendiente"}</p>
            <p className="mt-1 text-sm text-slate-500">{selectedDiagram?.name ?? "Diagrama pendiente"}</p>
          </Panel>

          <Panel className="p-5">
            <Database className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Modelo intermedio</h2>
            <p className="mt-2 break-all text-sm text-slate-600">{transformation?.id ?? "Sin transformacion activa"}</p>
            <div className="mt-4">
              <StatusBadge tone={transformation ? "success" : "neutral"}>{transformation?.status ?? "pendiente"}</StatusBadge>
            </div>
          </Panel>

          <Panel className="p-5">
            <Code2 className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Spring Boot</h2>
            <p className="mt-2 text-sm text-slate-600">{backend?.name ?? "Disponible despues de transformar"}</p>
            {backend && (
              <p className="mt-2 text-xs text-slate-500">
                {backend.manifest.file_count ?? 0} archivos, PostgreSQL {String(backend.manifest.database_name ?? "")}
              </p>
            )}
            <Button className="mt-4" disabled={!transformation || loading === "backend"} onClick={generateBackend} variant="secondary">
              {loading === "backend" ? "Generando" : "Generar backend"}
            </Button>
            <Button className="mt-2 w-full" disabled={!backend} icon={<Download size={18} aria-hidden="true" />} onClick={downloadBackend} variant="ghost">
              Descargar ZIP
            </Button>
          </Panel>

          <Panel className="p-5">
            <Smartphone className="text-accent" aria-hidden="true" />
            <h2 className="mt-4 text-lg font-semibold">Flutter</h2>
            <p className="mt-2 text-sm text-slate-600">{frontend?.name ?? (backend ? "Disponible" : "Genere backend primero")}</p>
            {backend && (
              <Input
                className="mt-3"
                label="URL backend para app"
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrl(event.target.value)}
              />
            )}
            {frontend && (
              <p className="mt-2 text-xs text-slate-500">
                {frontend.manifest.file_count ?? 0} archivos, API {String(frontend.manifest.api_base_url ?? "")}
              </p>
            )}
            <Button className="mt-4" disabled={!backend || loading === "frontend"} onClick={generateFrontend} variant="secondary">
              {loading === "frontend" ? "Generando" : "Generar frontend"}
            </Button>
            <Button className="mt-2 w-full" disabled={!frontend} icon={<Download size={18} aria-hidden="true" />} onClick={downloadFrontend} variant="ghost">
              Descargar ZIP
            </Button>
          </Panel>
        </div>
      </div>

      <Panel className="p-5">
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="grid gap-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-accent">
                  <Palette size={18} aria-hidden="true" />
                  <h2 className="text-lg font-semibold text-ink">Estilo Flutter</h2>
                </div>
                <p className="mt-1 text-sm text-slate-600">
                  Ajustes visuales que se aplican al ZIP Flutter generado.
                </p>
              </div>
              <Button onClick={() => setThemeConfig(defaultThemeConfig)} variant="ghost">
                Restablecer
              </Button>
            </div>

            <div className="grid gap-2 sm:grid-cols-3">
              {presetThemes.map((preset) => (
                <Button
                  key={preset.name}
                  onClick={() => setThemeConfig(preset.config)}
                  variant="secondary"
                >
                  {preset.name}
                </Button>
              ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              <Input
                label="Color primario"
                type="color"
                value={themeConfig.primary_color}
                onChange={(event) => updateThemeConfig({ primary_color: event.target.value })}
              />
              <Input
                label="Color secundario"
                type="color"
                value={themeConfig.secondary_color}
                onChange={(event) => updateThemeConfig({ secondary_color: event.target.value })}
              />
              <Input
                label="Fondo"
                type="color"
                value={themeConfig.background_color}
                onChange={(event) => updateThemeConfig({ background_color: event.target.value })}
              />
              <Input
                label="Superficie"
                type="color"
                value={themeConfig.surface_color}
                onChange={(event) => updateThemeConfig({ surface_color: event.target.value })}
              />
              <Input
                label="Botones"
                type="color"
                value={themeConfig.button_color}
                onChange={(event) => updateThemeConfig({ button_color: event.target.value })}
              />

              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Fuente
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                  value={themeConfig.font_family}
                  onChange={(event) => updateThemeConfig({ font_family: event.target.value })}
                >
                  {fontOptions.map((font) => (
                    <option key={font} value={font}>
                      {font}
                    </option>
                  ))}
                </select>
              </label>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Estilo de boton
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                  value={themeConfig.button_style}
                  onChange={(event) => updateThemeConfig({ button_style: event.target.value as FlutterThemeConfig["button_style"] })}
                >
                  <option value="filled">Solido</option>
                  <option value="outline">Contorno</option>
                  <option value="tonal">Tonal</option>
                </select>
              </label>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Densidad
                <select
                  className="h-10 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
                  value={themeConfig.density}
                  onChange={(event) => updateThemeConfig({ density: event.target.value as FlutterThemeConfig["density"] })}
                >
                  <option value="compact">Compacta</option>
                  <option value="normal">Normal</option>
                  <option value="comfortable">Amplia</option>
                </select>
              </label>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Radio de bordes: {themeConfig.border_radius}px
                <input
                  className="h-10 accent-teal-700"
                  max={32}
                  min={0}
                  type="range"
                  value={themeConfig.border_radius}
                  onChange={(event) => updateThemeConfig({ border_radius: Number(event.target.value) })}
                />
              </label>
            </div>
          </div>

          <div
            className="min-h-[520px] rounded-md border border-slate-200 p-4"
            style={{
              backgroundColor: themeConfig.background_color,
              color: previewForeground,
              fontFamily: themeConfig.font_family
            }}
          >
            <div
              className="mx-auto flex h-full max-w-[300px] flex-col overflow-hidden border border-slate-300 shadow-sm"
              style={{
                backgroundColor: themeConfig.background_color,
                borderRadius: Math.max(18, themeConfig.border_radius + 8)
              }}
            >
              <div
                className="px-4"
                style={{
                  backgroundColor: themeConfig.primary_color,
                  color: appBarForeground,
                  paddingBottom: previewDensity.padding,
                  paddingTop: previewDensity.padding
                }}
              >
                <p className="text-xs opacity-80">AppBar</p>
                <h3 className="truncate text-lg font-semibold">{name || "AplicacionGenerada"}</h3>
              </div>
              <div
                className="grid flex-1"
                style={{
                  gap: previewDensity.gap,
                  padding: previewDensity.padding
                }}
              >
                <div
                  className="border shadow-sm"
                  style={{ backgroundColor: themeConfig.surface_color, borderRadius: themeConfig.border_radius }}
                >
                  <div className="flex items-center gap-3 p-3">
                    <span
                      className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold"
                      style={{ backgroundColor: `${themeConfig.secondary_color}33`, color: themeConfig.secondary_color }}
                    >
                      C
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold">Cliente</p>
                      <p className="truncate text-sm opacity-70">nombre: Ana | correo: ana@app.com</p>
                    </div>
                    <span className="text-lg opacity-60">...</span>
                  </div>
                </div>

                <label className="grid gap-1 text-sm">
                  Nombre
                  <span
                    className="flex items-center border px-3 text-sm opacity-80"
                    style={{
                      backgroundColor: themeConfig.surface_color,
                      borderColor: `${themeConfig.primary_color}55`,
                      borderRadius: themeConfig.border_radius,
                      height: previewDensity.fieldHeight
                    }}
                  >
                    Cliente demo
                  </span>
                </label>

                <label className="grid gap-1 text-sm">
                  Curso
                  <span
                    className="flex items-center justify-between border px-3 text-sm"
                    style={{
                      backgroundColor: themeConfig.surface_color,
                      borderColor: `${themeConfig.primary_color}55`,
                      borderRadius: themeConfig.border_radius,
                      height: previewDensity.fieldHeight
                    }}
                  >
                    Arquitectura de software
                    <span className="opacity-60">v</span>
                  </span>
                </label>

                <div
                  className="flex items-center justify-between border px-3 text-sm"
                  style={{
                    backgroundColor: themeConfig.surface_color,
                    borderColor: `${themeConfig.primary_color}33`,
                    borderRadius: themeConfig.border_radius,
                    minHeight: previewDensity.fieldHeight
                  }}
                >
                  <span>activo</span>
                  <span
                    className="flex h-6 w-11 items-center rounded-full p-1"
                    style={{ backgroundColor: `${themeConfig.button_color}59` }}
                  >
                    <span
                      className="h-4 w-4 rounded-full"
                      style={{ backgroundColor: themeConfig.button_color, marginLeft: 16 }}
                    />
                  </span>
                </div>

                <button
                  className="mt-auto h-12 px-4 text-sm font-semibold transition"
                  style={actionButtonStyle}
                  type="button"
                >
                  Guardar
                </button>

                <div
                  className="ml-auto grid h-12 w-12 place-items-center rounded-full text-xl shadow-sm"
                  style={{ backgroundColor: themeConfig.button_color, color: readableTextColor(themeConfig.button_color) }}
                >
                  +
                </div>
              </div>
            </div>
          </div>
        </div>
      </Panel>
    </section>
  );
}
