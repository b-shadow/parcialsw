import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ArrowLeft, CalendarDays, CheckCircle2, Download, LoaderCircle, PackageOpen, Palette, RefreshCw, Server, Smartphone } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../../../shared/components/Button";
import { Panel } from "../../../shared/components/Panel";
import { StatusBadge } from "../../../shared/components/StatusBadge";
import { cn } from "../../../shared/utils/cn";
import { projectService } from "../../gestion_proyectos_colaboracion/services/projectService";
import type { Project } from "../../gestion_proyectos_colaboracion/types/project";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import { FlutterStyleWorkspace } from "../components/FlutterStyleWorkspace";
import { generationService } from "../services/generationService";
import { defaultThemeV2 } from "../theme/themeContract";
import type { FlutterThemeConfig, GeneratedBackend, GeneratedFrontend } from "../types/generation";

type GenerationTab = "backend" | "frontend";
type BusyAction = "loading" | "backend" | "frontend" | "download" | "";

function formattedDate(value: string) {
  return new Intl.DateTimeFormat("es-BO", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function statusTone(status: string): "neutral" | "success" | "warning" | "danger" {
  if (status === "generated" || status === "verified") return "success";
  if (status === "failed") return "danger";
  if (status === "generating") return "warning";
  return "neutral";
}

function downloadBlob(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function GenerationPage() {
  const { projectId = "" } = useParams();
  const [activeTab, setActiveTab] = useState<GenerationTab>("backend");
  const [project, setProject] = useState<Project | null>(null);
  const [diagramId, setDiagramId] = useState("");
  const [backends, setBackends] = useState<GeneratedBackend[]>([]);
  const [frontends, setFrontends] = useState<GeneratedFrontend[]>([]);
  const [selectedBackendId, setSelectedBackendId] = useState("");
  const [apiBaseUrl, setApiBaseUrl] = useState("http://10.0.2.2:8080");
  const [themeConfig, setThemeConfig] = useState<FlutterThemeConfig>(defaultThemeV2);
  const [previewTransformationId, setPreviewTransformationId] = useState<string>();
  const [busy, setBusy] = useState<BusyAction>("loading");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const backendById = useMemo(() => new Map(backends.map((backend) => [backend.id, backend])), [backends]);
  const generatedBackends = useMemo(() => backends.filter((backend) => backend.status === "generated"), [backends]);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    async function load() {
      setBusy("loading");
      setError("");
      try {
        const [loadedProject, diagrams, backendHistory, frontendHistory] = await Promise.all([
          projectService.get(projectId), umlService.listDiagrams(projectId),
          generationService.backends(projectId), generationService.frontends(projectId)
        ]);
        if (cancelled) return;
        setProject(loadedProject);
        setDiagramId(diagrams[0]?.id ?? "");
        setBackends(backendHistory);
        setFrontends(frontendHistory);
        setSelectedBackendId(backendHistory.find((item) => item.status === "generated")?.id ?? "");
        setPreviewTransformationId(frontendHistory[0]?.transformation_id);
        if (!diagrams[0]) setError("El proyecto no tiene un diagrama UML disponible para generar codigo.");
      } catch {
        if (!cancelled) setError("No se pudo cargar la generacion del proyecto.");
      } finally {
        if (!cancelled) setBusy("");
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [projectId]);

  async function refreshHistory() {
    const [backendHistory, frontendHistory] = await Promise.all([
      generationService.backends(projectId), generationService.frontends(projectId)
    ]);
    setBackends(backendHistory);
    setFrontends(frontendHistory);
    return { backendHistory, frontendHistory };
  }

  async function generateBackend() {
    if (!diagramId || !project) return;
    setBusy("backend"); setError(""); setMessage("");
    try {
      const transformation = await generationService.transform({ diagram_id: diagramId, target_platform: "spring_boot" });
      const generated = await generationService.springBoot({ transformation_id: transformation.id, name: project.name, version_label: "auto" });
      const history = await refreshHistory();
      setSelectedBackendId(generated.id);
      setBackends(history.backendHistory);
      setMessage(`${generated.name} fue generado y guardado correctamente.`);
    } catch {
      setError("No se pudo generar el backend. Revise que el diagrama sea valido e intente nuevamente.");
      await refreshHistory().catch(() => undefined);
    } finally { setBusy(""); }
  }

  async function generateFrontend() {
    if (!diagramId || !project || !selectedBackendId) return;
    setBusy("frontend"); setError(""); setMessage("");
    try {
      const transformation = await generationService.transform({ diagram_id: diagramId, target_platform: "flutter" });
      const generated = await generationService.flutter({
        transformation_id: transformation.id, name: project.name, version_label: "auto",
        backend_id: selectedBackendId, api_base_url: apiBaseUrl.trim() || undefined, theme_config: themeConfig
      });
      setPreviewTransformationId(transformation.id);
      const history = await refreshHistory();
      setFrontends(history.frontendHistory);
      setMessage(`${generated.name} fue generado y guardado correctamente.`);
    } catch {
      setError("No se pudo generar Flutter. Revise el diagrama, el backend elegido y la configuracion visual.");
      await refreshHistory().catch(() => undefined);
    } finally { setBusy(""); }
  }

  async function downloadBackend(backend: GeneratedBackend) {
    setBusy("download"); setError("");
    try { downloadBlob(await generationService.downloadSpringBoot(backend.id), `${backend.name}.zip`); }
    catch { setError("No se pudo descargar ese backend."); }
    finally { setBusy(""); }
  }

  async function downloadFrontend(frontend: GeneratedFrontend) {
    setBusy("download"); setError("");
    try { downloadBlob(await generationService.downloadFlutter(frontend.id), `${frontend.name}.zip`); }
    catch { setError("No se pudo descargar esa aplicacion Flutter."); }
    finally { setBusy(""); }
  }

  const nextBackendVersion = `v${backends.length + 1}`;
  const nextFrontendVersion = `v${frontends.length + 1}`;

  return (
    <section className="grid gap-5">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Link className="mb-3 inline-flex items-center gap-2 text-sm font-medium text-accent hover:underline" to="/proyectos">
            <ArrowLeft size={16} aria-hidden="true" /> Volver a proyectos
          </Link>
          <h1 className="text-2xl font-black text-blue-950 dark:text-white">Generacion de codigo</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            {project ? `${project.name}: genera y conserva cada version del backend y de Flutter.` : "Cargando proyecto..."}
          </p>
        </div>
        <Button disabled={busy !== ""} icon={<RefreshCw className={busy === "loading" ? "animate-spin" : ""} size={17} />} onClick={() => void refreshHistory()} variant="secondary">
          Actualizar historial
        </Button>
      </header>

      {error && <p className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}
      {message && <p className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700"><CheckCircle2 size={17} />{message}</p>}

      <div className="grid grid-cols-2 overflow-hidden rounded-md border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <TabButton active={activeTab === "backend"} icon={<Server size={18} />} label="Backend" onClick={() => setActiveTab("backend")} />
        <TabButton active={activeTab === "frontend"} icon={<Smartphone size={18} />} label="Frontend Flutter" onClick={() => setActiveTab("frontend")} />
      </div>

      {activeTab === "backend" ? (
        <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
          <Panel className="h-fit p-5 dark:border-slate-700 dark:bg-slate-900">
            <SectionTitle icon={<Server size={22} />} title="Generar backend" subtitle="Java y Spring Boot" />
            <dl className="mt-5 grid gap-3 border-y border-slate-200 py-4 text-sm dark:border-slate-700">
              <InfoRow label="Siguiente version" value={nextBackendVersion} />
              <InfoRow label="Nombre" value={`${project?.name ?? "Proyecto"}_${nextBackendVersion}`} />
              <InfoRow label="Origen" value="Diagrama actual" />
            </dl>
            <Button className="mt-5 w-full" disabled={!diagramId || busy !== ""} icon={busy === "backend" ? <LoaderCircle className="animate-spin" size={18} /> : <PackageOpen size={18} />} onClick={() => void generateBackend()}>
              {busy === "backend" ? "Generando backend..." : "Generar nueva version"}
            </Button>
          </Panel>
          <GenerationHistory emptyMessage="Aun no se genero ningun backend para este proyecto." title="Versiones de backend">
            {backends.map((backend) => <HistoryRow createdAt={backend.created_at} disabled={!backend.artifact_path || backend.status !== "generated" || busy === "download"} key={backend.id} name={backend.name} onDownload={() => void downloadBackend(backend)} status={backend.status} subtitle={`Spring Boot | ${backend.manifest.file_count ?? 0} archivos`} version={backend.version_label} />)}
          </GenerationHistory>
        </div>
      ) : (
        <div className="grid gap-5">
          <div className="grid gap-5 xl:grid-cols-[420px_minmax(0,1fr)]">
            <Panel className="h-fit p-5 dark:border-slate-700 dark:bg-slate-900">
              <SectionTitle icon={<Smartphone size={22} />} title="Generar Flutter" subtitle={`Siguiente version: ${project?.name ?? "Proyecto"}_${nextFrontendVersion}`} />
              <label className="mt-5 grid gap-1.5 text-sm font-semibold">Version del backend
                <select className="h-11 rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 dark:border-slate-700 dark:bg-slate-950" onChange={(event) => setSelectedBackendId(event.target.value)} value={selectedBackendId}>
                  <option value="">Seleccione un backend generado</option>
                  {generatedBackends.map((backend) => <option key={backend.id} value={backend.id}>{backend.name} ({backend.version_label})</option>)}
                </select>
              </label>
              <label className="mt-4 grid gap-1.5 text-sm font-semibold">URL del backend para la app
                <input className="h-11 rounded-md border border-slate-300 bg-transparent px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20 dark:border-slate-700" onChange={(event) => setApiBaseUrl(event.target.value)} value={apiBaseUrl} />
              </label>
              <Button className="mt-5 w-full" disabled={!diagramId || !selectedBackendId || busy !== ""} icon={busy === "frontend" ? <LoaderCircle className="animate-spin" size={18} /> : <PackageOpen size={18} />} onClick={() => void generateFrontend()}>
                {busy === "frontend" ? "Generando Flutter..." : "Generar nueva version"}
              </Button>
              {!generatedBackends.length && <p className="mt-3 text-xs text-amber-700">Primero genere al menos una version del backend.</p>}
            </Panel>
            <GenerationHistory emptyMessage="Aun no se genero ninguna aplicacion Flutter para este proyecto." title="Versiones de Flutter">
              {frontends.map((frontend) => {
                const backend = frontend.backend_id ? backendById.get(frontend.backend_id) : undefined;
                return <HistoryRow createdAt={frontend.created_at} disabled={!frontend.artifact_path || frontend.status !== "generated" || busy === "download"} key={frontend.id} name={frontend.name} onDownload={() => void downloadFrontend(frontend)} status={frontend.status} subtitle={backend ? `Creado para backend ${backend.name} (${backend.version_label})` : "Backend de origen no disponible"} version={frontend.version_label} />;
              })}
            </GenerationHistory>
          </div>
          <section>
            <div className="mb-4 flex items-center gap-3"><Palette className="text-accent" size={22} /><div><h2 className="font-bold text-blue-950 dark:text-white">Estilo de la aplicacion Flutter</h2><p className="text-sm text-slate-500 dark:text-slate-400">Configura y previsualiza el tema usado en la siguiente generacion.</p></div></div>
            <FlutterStyleWorkspace onChange={setThemeConfig} projectId={projectId} transformationId={previewTransformationId} value={themeConfig} />
          </section>
        </div>
      )}
    </section>
  );
}

function TabButton({ active, icon, label, onClick }: { active: boolean; icon: ReactNode; label: string; onClick: () => void }) {
  return <button className={cn("flex h-12 items-center justify-center gap-2 border-r border-slate-200 text-sm font-bold transition last:border-r-0 dark:border-slate-700", active ? "bg-accent text-white" : "text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800")} onClick={onClick} type="button">{icon}{label}</button>;
}

function SectionTitle({ icon, subtitle, title }: { icon: ReactNode; subtitle: string; title: string }) {
  return <div className="flex items-center gap-3"><span className="grid size-11 place-items-center rounded-md bg-teal-50 text-accent dark:bg-teal-400/10 dark:text-teal-300">{icon}</span><div><h2 className="font-bold text-blue-950 dark:text-white">{title}</h2><p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p></div></div>;
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return <div className="flex justify-between gap-3"><dt className="text-slate-500">{label}</dt><dd className="truncate font-bold">{value}</dd></div>;
}

function GenerationHistory({ children, emptyMessage, title }: { children: ReactNode; emptyMessage: string; title: string }) {
  const hasChildren = Array.isArray(children) ? children.length > 0 : Boolean(children);
  return <Panel className="min-w-0 overflow-hidden dark:border-slate-700 dark:bg-slate-900"><header className="flex items-center gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-700"><PackageOpen className="text-accent" size={21} /><h2 className="font-bold text-blue-950 dark:text-white">{title}</h2></header>{hasChildren ? <div className="divide-y divide-slate-200 dark:divide-slate-700">{children}</div> : <p className="px-5 py-12 text-center text-sm text-slate-500">{emptyMessage}</p>}</Panel>;
}

function HistoryRow({ createdAt, disabled, name, onDownload, status, subtitle, version }: { createdAt: string; disabled: boolean; name: string; onDownload: () => void; status: string; subtitle: string; version: string }) {
  return <div className="grid gap-3 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><p className="truncate font-bold text-slate-900 dark:text-white">{name}</p><StatusBadge tone={statusTone(status)}>{status}</StatusBadge><span className="text-xs font-bold text-blue-700 dark:text-blue-300">{version}</span></div><p className="mt-1 truncate text-sm text-slate-600 dark:text-slate-300">{subtitle}</p><p className="mt-1 flex items-center gap-1.5 text-xs text-slate-500"><CalendarDays size={14} />{formattedDate(createdAt)}</p></div><Button aria-label={`Descargar ${name}`} className="w-full sm:w-auto" disabled={disabled} icon={<Download size={17} />} onClick={onDownload} title={`Descargar ${name}`} variant="secondary">Descargar</Button></div>;
}
