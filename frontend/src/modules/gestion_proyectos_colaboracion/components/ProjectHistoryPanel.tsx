import { useCallback, useEffect, useMemo, useState } from "react";
import { ArchiveRestore, GitCommitHorizontal, History, LoaderCircle, Plus, RefreshCw, Save, X } from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { cn } from "../../../shared/utils/cn";
import { projectService } from "../services/projectService";
import type { CollaborationChange, Project, ProjectVersion, RestorePreview, VersionRestoreResult } from "../types/project";

type Props = {
  projectId: string;
  onVersionRestored?: (result: VersionRestoreResult) => void | Promise<void>;
  mode?: "floating" | "embedded";
};
type Dialog = { type: "save" } | { type: "restore"; version: ProjectVersion; preview?: RestorePreview } | null;

const labels: Record<string, string> = {
  UML_CLASS_CREATED: "Creo una clase", UML_CLASS_UPDATED: "Edito una clase", UML_CLASS_DELETED: "Elimino una clase",
  UML_ATTRIBUTE_CREATED: "Agrego un atributo", UML_ATTRIBUTE_UPDATED: "Edito un atributo", UML_ATTRIBUTE_DELETED: "Elimino un atributo",
  UML_METHOD_CREATED: "Agrego un metodo", UML_METHOD_UPDATED: "Edito un metodo", UML_METHOD_DELETED: "Elimino un metodo",
  UML_RELATIONSHIP_CREATED: "Creo una relacion", UML_RELATIONSHIP_UPDATED: "Edito una relacion", UML_RELATIONSHIP_DELETED: "Elimino una relacion",
  UML_ELEMENT_MOVED: "Movio un elemento", AI_ACTIONS_APPLIED: "Aplico cambios con IA",
  METHOD_SPEC_UPDATED: "Actualizo la especificacion de un metodo", FLUTTER_THEME_UPDATED: "Actualizo el estilo Flutter",
  PROJECT_VERSION_CREATED: "Guardo una version", PROJECT_VERSION_RESTORED: "Restauro una version",
  PROJECT_MEMBER_ADDED: "Agrego un miembro", PROJECT_MEMBER_ROLE_CHANGED: "Cambio un rol", PROJECT_MEMBER_REMOVED: "Retiro un miembro",
  CREATE_CLASS: "Creo una clase", UPDATE_CLASS: "Edito una clase", DELETE_CLASS: "Elimino una clase", RESTORE_VERSION: "Restauro una version"
};

const formatMoment = (value: string) => new Intl.DateTimeFormat("es", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));

export function ProjectHistoryPanel({ projectId, onVersionRestored, mode = "floating" }: Props) {
  const embedded = mode === "embedded";
  const currentUser = useAuthStore((state) => state.user);
  const [open, setOpen] = useState(embedded);
  const [view, setView] = useState<"activity" | "versions">("activity");
  const [project, setProject] = useState<Project | null>(null);
  const [canManage, setCanManage] = useState(false);
  const [activity, setActivity] = useState<CollaborationChange[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [versions, setVersions] = useState<ProjectVersion[]>([]);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const [loadedProject, members, page] = await Promise.all([
      projectService.get(projectId), projectService.members(projectId), projectService.activity(projectId)
    ]);
    const allowed = loadedProject.owner_id === currentUser?.id || members.some((member) => member.user_id === currentUser?.id && member.project_role === "ORGANIZADOR");
    setProject(loadedProject);
    setCanManage(allowed);
    setActivity(page.items);
    setCursor(page.next_cursor);
    setHasMore(page.has_more);
    setVersions(allowed ? await projectService.versions(projectId) : []);
  }, [currentUser?.id, projectId]);

  useEffect(() => { if (open) void load().catch(() => setMessage("No se pudo cargar el historial.")); }, [load, open]);
  useEffect(() => {
    const listener = (raw: Event) => {
      const detail = (raw as CustomEvent<Record<string, unknown>>).detail;
      if (detail?.project_id === projectId && ["PROJECT_ACTIVITY_APPENDED", "PROJECT_VERSION_CREATED", "PROJECT_VERSION_RESTORED", "PROJECT_STATE_INVALIDATED", "UML_EVENT"].includes(String(detail.type)) && open) {
        void load().catch(() => undefined);
      }
    };
    window.addEventListener("case:project-socket-event", listener);
    return () => window.removeEventListener("case:project-socket-event", listener);
  }, [load, open, projectId]);

  const visibleView = useMemo(() => view === "versions" && !canManage ? "activity" : view, [canManage, view]);

  async function more() {
    if (!cursor) return;
    const page = await projectService.activity(projectId, cursor);
    setActivity((current) => [...current, ...page.items]);
    setCursor(page.next_cursor);
    setHasMore(page.has_more);
  }

  async function saveVersion() {
    if (!name.trim() || !project) return;
    setBusy(true); setMessage("");
    try {
      const version = await projectService.saveVersion(projectId, { name: name.trim(), description: description.trim() || undefined, expected_project_revision: project.revision });
      setVersions((current) => [version, ...current]);
      setDialog(null); setName(""); setDescription("");
      setMessage(`Version ${version.version_number} guardada.`);
    } catch { setMessage("No se pudo guardar. Verifica si existen cambios desde la ultima version."); }
    finally { setBusy(false); }
  }

  async function inspect(version: ProjectVersion) {
    setBusy(true); setMessage(""); setDialog({ type: "restore", version });
    try { setDialog({ type: "restore", version, preview: await projectService.restorePreview(projectId, version.id) }); }
    catch { setDialog(null); setMessage("No se pudo inspeccionar la version."); }
    finally { setBusy(false); }
  }

  async function restore(version: ProjectVersion, preview: RestorePreview) {
    setBusy(true); setMessage("");
    try {
      const result = await projectService.restoreVersion(projectId, version.id, preview.current_revision);
      setDialog(null);
      setMessage(`Version ${version.version_number} restaurada. Respaldo v${result.backup_version.version_number} creado.`);
      await load(); await onVersionRestored?.(result);
    } catch { setMessage("No se pudo restaurar. Recarga la vista previa si el proyecto cambio."); }
    finally { setBusy(false); }
  }

  return <>
    {!embedded ? <button aria-label="Abrir actividad del proyecto" className="fixed bottom-24 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-teal-700 text-white shadow-lg hover:bg-teal-800 focus:ring-2 focus:ring-teal-400" onClick={() => setOpen((value) => !value)} title="Actividad y versiones" type="button"><History size={22} /></button> : null}
    {open ? <aside className={cn(
      "flex min-h-0 flex-col overflow-hidden",
      embedded
        ? "h-full w-full bg-transparent"
        : "fixed bottom-40 right-4 z-40 max-h-[min(680px,75vh)] w-[min(420px,calc(100vw-2rem))] rounded-md border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-950 sm:right-6"
    )}>
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700"><div><h2 className="text-sm font-bold">Actividad del proyecto</h2><p className="mt-1 text-xs text-slate-500">Trazabilidad continua y versiones guardadas</p></div><div className="flex gap-1"><button aria-label="Actualizar" className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => void load()} title="Actualizar" type="button"><RefreshCw size={17} /></button>{!embedded ? <button aria-label="Cerrar" className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => setOpen(false)} title="Cerrar" type="button"><X size={18} /></button> : null}</div></header>
      {canManage ? <div className="grid grid-cols-2 border-b border-slate-200 p-2 dark:border-slate-700"><button className={cn("h-9 rounded-md text-xs font-bold", visibleView === "activity" ? "bg-teal-700 text-white" : "text-slate-600 dark:text-slate-300")} onClick={() => setView("activity")} type="button">Actividad</button><button className={cn("h-9 rounded-md text-xs font-bold", visibleView === "versions" ? "bg-teal-700 text-white" : "text-slate-600 dark:text-slate-300")} onClick={() => setView("versions")} type="button">Versiones</button></div> : null}
      <div className="overflow-y-auto p-3">{visibleView === "activity" ? <div className="grid gap-1">{activity.map((item) => <article className="border-b border-slate-100 px-1 py-3 last:border-0 dark:border-slate-800" key={item.id}><div className="flex items-start gap-3"><GitCommitHorizontal className="mt-0.5 shrink-0 text-teal-700" size={17} /><div className="min-w-0 flex-1"><div className="flex justify-between gap-3"><p className="text-sm font-bold">{item.user_name}</p><time className="shrink-0 text-[11px] text-slate-400">{formatMoment(item.created_at)}</time></div><p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{labels[item.event_type] ?? "Actualizo el proyecto"}</p>{item.resource_type ? <p className="mt-1 text-[11px] text-slate-400">{item.resource_type}</p> : null}</div></div></article>)}{!activity.length ? <p className="py-8 text-center text-sm text-slate-500">Aun no hay actividad registrada.</p> : null}{hasMore ? <button className="mt-2 h-10 rounded-md border border-slate-300 text-sm font-bold text-teal-700" onClick={() => void more()} type="button">Cargar anteriores</button> : null}</div> : <div className="grid gap-3"><button className="flex h-11 items-center justify-center gap-2 rounded-md bg-teal-700 text-sm font-bold text-white hover:bg-teal-800" onClick={() => setDialog({ type: "save" })} type="button"><Plus size={17} /> Guardar version</button>{versions.map((version) => <article className="rounded-md border border-slate-200 p-3 dark:border-slate-700" key={version.id}><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-bold">v{version.version_number} · {version.name}</p><p className="mt-1 text-xs text-slate-500">{version.created_by_name ?? "Miembro"} · {formatMoment(version.created_at)}</p><p className="mt-1 text-[11px] uppercase text-slate-400">{version.kind === "pre_restore_backup" ? "Respaldo automatico" : "Version manual"}</p></div><button aria-label={`Restaurar version ${version.version_number}`} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-teal-700 text-teal-700 hover:bg-teal-50 dark:hover:bg-slate-800" onClick={() => void inspect(version)} title="Inspeccionar y restaurar" type="button"><ArchiveRestore size={17} /></button></div>{version.description ? <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">{version.description}</p> : null}</article>)}</div>}</div>
      {message ? <p aria-live="polite" className="border-t border-slate-200 px-4 py-3 text-xs dark:border-slate-700">{message}</p> : null}
    </aside> : null}
    {dialog ? <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/55 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) setDialog(null); }}><section aria-modal="true" className="w-full max-w-lg rounded-md bg-white p-5 shadow-2xl dark:bg-slate-950" role="dialog"><header className="flex items-center justify-between"><h2 className="text-base font-bold">{dialog.type === "save" ? "Guardar version" : `Restaurar v${dialog.version.version_number}`}</h2><button aria-label="Cerrar dialogo" className="flex h-9 w-9 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" disabled={busy} onClick={() => setDialog(null)} title="Cerrar" type="button"><X size={18} /></button></header>{dialog.type === "save" ? <div className="mt-4 grid gap-4"><p className="text-sm text-slate-600 dark:text-slate-300">Se capturaran diagramas, especificaciones de metodos, tema y configuracion no sensible. Revision actual: {project?.revision ?? 0}.</p><label className="grid gap-1 text-sm font-semibold">Nombre<input autoFocus className="rounded-md border border-slate-300 bg-transparent px-3 py-2" maxLength={120} onChange={(event) => setName(event.target.value)} value={name} /></label><label className="grid gap-1 text-sm font-semibold">Descripcion opcional<textarea className="min-h-20 rounded-md border border-slate-300 bg-transparent px-3 py-2" onChange={(event) => setDescription(event.target.value)} value={description} /></label><button className="flex h-11 items-center justify-center gap-2 rounded-md bg-teal-700 font-bold text-white disabled:opacity-50" disabled={busy || !name.trim()} onClick={() => void saveVersion()} type="button">{busy ? <LoaderCircle className="animate-spin" size={17} /> : <Save size={17} />} Guardar</button></div> : <div className="mt-4">{dialog.preview ? <><p className="text-sm text-slate-600 dark:text-slate-300">Se creara un respaldo automatico. La conversacion de IA, miembros, bitacora, notificaciones y artefactos no cambiaran.</p><dl className="mt-4 grid grid-cols-2 gap-2 text-sm">{Object.entries(dialog.preview.summary).map(([key, value]) => <div className="rounded-md border border-slate-200 p-3 dark:border-slate-700" key={key}><dt className="text-xs capitalize text-slate-500">{key}</dt><dd className="mt-1 font-bold">{value}</dd></div>)}</dl>{dialog.preview.warnings.length ? <p className="mt-3 text-xs text-amber-700">Compatibilidad: {dialog.preview.warnings.join(", ")}</p> : null}<button className="mt-5 flex h-11 w-full items-center justify-center gap-2 rounded-md bg-red-700 font-bold text-white disabled:opacity-50" disabled={busy} onClick={() => void restore(dialog.version, dialog.preview!)} type="button">{busy ? <LoaderCircle className="animate-spin" size={17} /> : <ArchiveRestore size={17} />} Restaurar version</button></> : <p className="flex items-center gap-2 py-8 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={17} /> Calculando diferencias</p>}</div>}</section></div> : null}
  </>;
}
