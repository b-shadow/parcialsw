import { useEffect, useRef, useState } from "react";
import { ChevronDown, Circle, Users, X } from "lucide-react";

import { useProjectAiStore } from "../store/projectAiStore";

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "U";
  return parts.slice(0, 2).map((part) => part[0]).join("").toUpperCase();
}

function roleLabel(role: string) {
  if (role === "ORGANIZADOR") return "Organizador";
  if (role === "EDITOR") return "Editor";
  return role;
}

export function ProjectPresenceIndicator() {
  const presence = useProjectAiStore((state) => state.presence);
  const socketStatus = useProjectAiStore((state) => state.socketStatus);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const connected = socketStatus === "connected";

  useEffect(() => {
    if (!open) return;
    function closeOutside(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function closeWithEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", closeOutside);
    window.addEventListener("keydown", closeWithEscape);
    return () => {
      document.removeEventListener("mousedown", closeOutside);
      window.removeEventListener("keydown", closeWithEscape);
    };
  }, [open]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        aria-expanded={open}
        aria-label="Ver integrantes activos"
        className="inline-flex h-7 items-center gap-1.5 rounded-md px-1.5 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-50 dark:text-emerald-300 dark:hover:bg-emerald-950"
        onClick={() => setOpen((value) => !value)}
        title="Integrantes activos"
        type="button"
      >
        <Circle className={connected ? "fill-emerald-500 text-emerald-500" : "fill-amber-500 text-amber-500"} size={8} aria-hidden="true" />
        <span>{connected ? presence.length : 0}</span>
        <span className="hidden xl:inline">{presence.length === 1 ? "activo" : "activos"}</span>
        <ChevronDown className={`transition ${open ? "rotate-180" : ""}`} size={13} aria-hidden="true" />
      </button>

      {open && (
        <section className="absolute left-0 top-9 z-[70] w-72 max-w-[calc(100vw-32px)] overflow-hidden rounded-md border border-slate-200 bg-white text-slate-900 shadow-xl dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100" aria-label="Equipo activo">
          <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
            <div>
              <h2 className="text-sm font-bold">Equipo activo</h2>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                {connected ? `${presence.length} ${presence.length === 1 ? "persona conectada" : "personas conectadas"}` : "Reconectando..."}
              </p>
            </div>
            <button className="grid size-8 place-items-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => setOpen(false)} title="Cerrar" type="button">
              <X size={17} aria-hidden="true" />
            </button>
          </header>

          <div className="max-h-72 overflow-y-auto p-2">
            {connected && presence.length === 0 && (
              <p className="px-3 py-5 text-center text-sm text-slate-500 dark:text-slate-400">No hay integrantes activos.</p>
            )}
            {!connected && (
              <p className="px-3 py-5 text-center text-sm text-slate-500 dark:text-slate-400">Recuperando la conexión del equipo.</p>
            )}
            {connected && presence.map((member) => (
              <div className="flex items-center gap-3 rounded-md px-3 py-2.5 hover:bg-slate-50 dark:hover:bg-slate-800" key={member.user_id}>
                <span className="relative grid size-10 shrink-0 place-items-center rounded-full bg-blue-100 text-sm font-bold text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  {initials(member.display_name)}
                  <span className="absolute bottom-0 right-0 size-3 rounded-full border-2 border-white bg-emerald-500 dark:border-slate-900" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{member.display_name}</p>
                  <p className="truncate text-xs text-slate-500 dark:text-slate-400">{roleLabel(member.project_role)}</p>
                </div>
                {member.connection_count > 1 && (
                  <span className="text-xs text-slate-400" title="Sesiones abiertas">{member.connection_count} sesiones</span>
                )}
              </div>
            ))}
          </div>

          <footer className="flex items-center gap-2 border-t border-slate-200 px-4 py-2.5 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <Users size={14} aria-hidden="true" />
            Presencia actualizada en tiempo real
          </footer>
        </section>
      )}
    </div>
  );
}
