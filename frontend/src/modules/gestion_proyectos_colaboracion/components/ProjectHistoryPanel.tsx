import { useCallback, useEffect, useMemo, useState } from "react";
import { History, RefreshCw, RotateCcw, X } from "lucide-react";

import { useAuthStore } from "../../../core/auth/authStore";
import { cn } from "../../../shared/utils/cn";
import { projectService } from "../services/projectService";
import type {
  CollaborationChange,
  ProjectVersion,
  VersionRestoreResult
} from "../types/project";

type ProjectHistoryPanelProps = {
  projectId: string;
  onVersionRestored?: (result: VersionRestoreResult) => void | Promise<void>;
};

const actionLabels: Record<string, string> = {
  CREATE_CLASS: "Creo una clase",
  UPDATE_CLASS: "Edito una clase",
  DELETE_CLASS: "Elimino una clase",
  CREATE_ATTRIBUTE: "Agrego un atributo",
  UPDATE_ATTRIBUTE: "Edito un atributo",
  DELETE_ATTRIBUTE: "Elimino un atributo",
  CREATE_METHOD: "Agrego un metodo",
  UPDATE_METHOD: "Edito un metodo",
  DELETE_METHOD: "Elimino un metodo",
  CREATE_RELATION: "Creo una relacion",
  CREATE_RELATIONSHIP: "Creo una relacion",
  UPDATE_RELATIONSHIP: "Edito una relacion",
  DELETE_RELATIONSHIP: "Elimino una relacion",
  MOVE_ELEMENT: "Movio un elemento",
  AI_UPDATE_DIAGRAM: "Edito el diagrama con IA",
  RESTORE_VERSION: "Restauro una version"
};

function formatMoment(value: string) {
  return new Intl.DateTimeFormat("es", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function ProjectHistoryPanel({ projectId, onVersionRestored }: ProjectHistoryPanelProps) {
  const currentUser = useAuthStore((state) => state.user);
  const [isOpen, setIsOpen] = useState(false);
  const [changes, setChanges] = useState<CollaborationChange[]>([]);
  const [versions, setVersions] = useState<ProjectVersion[]>([]);
  const [isOrganizer, setIsOrganizer] = useState(false);
  const [activeView, setActiveView] = useState<"changes" | "versions">("changes");
  const [isBusy, setIsBusy] = useState(false);
  const [message, setMessage] = useState("");

  const loadHistory = useCallback(async () => {
    if (!projectId) return;
    const [members, recentChanges] = await Promise.all([
      projectService.members(projectId),
      projectService.changes(projectId)
    ]);
    const organizer = members.some(
      (member) => member.user_id === currentUser?.id && member.project_role === "ORGANIZADOR"
    );
    setIsOrganizer(organizer);
    setChanges(recentChanges);
    if (organizer) {
      setVersions(await projectService.versions(projectId));
    }
  }, [currentUser?.id, projectId]);

  useEffect(() => {
    if (!isOpen) return;
    void loadHistory().catch(() => setMessage("No se pudo cargar el historial."));
    const timer = window.setInterval(() => {
      void loadHistory().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [isOpen, loadHistory]);

  const visibleView = useMemo(
    () => (activeView === "versions" && !isOrganizer ? "changes" : activeView),
    [activeView, isOrganizer]
  );

  async function restore(version: ProjectVersion) {
    if (!window.confirm(`Restaurar la version ${version.version_number}? Se guardara un respaldo del estado actual.`)) {
      return;
    }
    setIsBusy(true);
    setMessage("");
    try {
      const result = await projectService.restoreVersion(projectId, version.id);
      setMessage(
        `Version ${result.restored_version.version_number} restaurada. Respaldo creado como v${result.backup_version.version_number}.`
      );
      await loadHistory();
      await onVersionRestored?.(result);
    } catch {
      setMessage("No se pudo restaurar la version.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <>
      <button
        aria-label="Abrir historial colaborativo"
        className="fixed bottom-24 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-teal-700 text-white shadow-lg transition hover:bg-teal-800 focus:outline-none focus:ring-2 focus:ring-teal-400"
        onClick={() => setIsOpen((current) => !current)}
        title="Historial colaborativo"
        type="button"
      >
        <History size={22} aria-hidden="true" />
      </button>

      {isOpen ? (
        <aside className="fixed bottom-40 right-6 z-40 flex max-h-[min(620px,70vh)] w-[min(390px,calc(100vw-2rem))] flex-col overflow-hidden rounded-md border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-950">
          <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <div>
              <h2 className="text-sm font-bold text-slate-950 dark:text-white">Historial colaborativo</h2>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {isOrganizer ? "Cambios y versiones guardadas" : "Cambios realizados en el proyecto"}
              </p>
            </div>
            <div className="flex gap-1">
              <button
                aria-label="Actualizar historial"
                className="flex h-9 w-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                onClick={() => void loadHistory()}
                title="Actualizar"
                type="button"
              >
                <RefreshCw size={17} aria-hidden="true" />
              </button>
              <button
                aria-label="Cerrar historial"
                className="flex h-9 w-9 items-center justify-center rounded-md text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                onClick={() => setIsOpen(false)}
                title="Cerrar"
                type="button"
              >
                <X size={18} aria-hidden="true" />
              </button>
            </div>
          </header>

          {isOrganizer ? (
            <div className="grid grid-cols-2 border-b border-slate-200 p-2 dark:border-slate-700">
              <button
                className={cn("h-9 rounded-md text-xs font-bold", visibleView === "changes" ? "bg-teal-700 text-white" : "text-slate-600 dark:text-slate-300")}
                onClick={() => setActiveView("changes")}
                type="button"
              >
                Cambios
              </button>
              <button
                className={cn("h-9 rounded-md text-xs font-bold", visibleView === "versions" ? "bg-teal-700 text-white" : "text-slate-600 dark:text-slate-300")}
                onClick={() => setActiveView("versions")}
                type="button"
              >
                Versiones
              </button>
            </div>
          ) : null}

          <div className="overflow-y-auto p-3">
            {visibleView === "changes" ? (
              <div className="grid gap-2">
                {changes.map((change) => (
                  <article className="border-b border-slate-100 px-1 py-3 last:border-0 dark:border-slate-800" key={change.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-slate-900 dark:text-white">{change.user_name}</p>
                        <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                          {actionLabels[change.event_type] ?? "Actualizo el diagrama"}
                        </p>
                      </div>
                      <time className="shrink-0 text-[11px] text-slate-400">{formatMoment(change.created_at)}</time>
                    </div>
                  </article>
                ))}
                {changes.length === 0 ? <p className="py-8 text-center text-sm text-slate-500">Aun no hay cambios registrados.</p> : null}
              </div>
            ) : (
              <div className="grid gap-3">
                {versions.map((version) => (
                  <article className="rounded-md border border-slate-200 p-3 dark:border-slate-700" key={version.id}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-slate-900 dark:text-white">v{version.version_number} · {version.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{version.created_by_name ?? "Miembro del proyecto"} · {formatMoment(version.created_at)}</p>
                      </div>
                      <button
                        aria-label={`Restaurar version ${version.version_number}`}
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-teal-700 text-teal-700 hover:bg-teal-50 disabled:opacity-50 dark:hover:bg-slate-800"
                        disabled={isBusy}
                        onClick={() => void restore(version)}
                        title={`Restaurar version ${version.version_number}`}
                        type="button"
                      >
                        <RotateCcw size={17} aria-hidden="true" />
                      </button>
                    </div>
                    {version.description ? <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">{version.description}</p> : null}
                  </article>
                ))}
                {versions.length === 0 ? <p className="py-8 text-center text-sm text-slate-500">Todavia no se guardaron versiones.</p> : null}
              </div>
            )}
          </div>
          {message ? <p className="border-t border-slate-200 px-4 py-3 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-300">{message}</p> : null}
        </aside>
      ) : null}
    </>
  );
}
