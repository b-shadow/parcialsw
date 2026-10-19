import { useEffect, useRef, useState } from "react";
import { AlertCircle, LoaderCircle, MessageSquare, MoreHorizontal, Pencil, Plus } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { phase1Service } from "../../../core/api/phase1Service";
import type { AiConversation } from "../../../core/contracts/phase1";
import { cn } from "../../../shared/utils/cn";
import { umlService } from "../../modelado_uml_inteligente/services/umlService";
import { projectService } from "../services/projectService";

export function ProjectWorkspacePage() {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();
  const menuRef = useRef<HTMLDivElement>(null);
  const [projectName, setProjectName] = useState("");
  const [diagramId, setDiagramId] = useState("");
  const [conversations, setConversations] = useState<AiConversation[]>([]);
  const [menuId, setMenuId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    async function loadWorkspace() {
      try {
        const [project, diagrams, chats] = await Promise.all([
          projectService.get(projectId),
          umlService.listDiagrams(projectId),
          phase1Service.conversations(projectId),
        ]);
        let diagram = diagrams[0];
        if (!diagram) {
          diagram = await umlService.createDiagram({
            project_id: projectId,
            name: project.name,
            description: project.description ?? undefined,
          });
        }
        if (!cancelled) {
          setProjectName(project.name);
          setDiagramId(diagram.id);
          setConversations(chats);
        }
      } catch {
        if (!cancelled) setError("No se pudieron cargar los chats del proyecto.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadWorkspace();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    function closeMenu(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuId(null);
      }
    }
    document.addEventListener("mousedown", closeMenu);
    return () => document.removeEventListener("mousedown", closeMenu);
  }, []);

  function openConversation(conversationId: string) {
    if (!diagramId || editingId) return;
    navigate(`/proyectos/${projectId}/uml/${diagramId}?panel=assistant&chat=${conversationId}`);
  }

  async function createConversation() {
    if (creating || !diagramId) return;
    setCreating(true);
    setError("");
    try {
      const conversation = await phase1Service.createConversation(projectId);
      openConversation(conversation.id);
    } catch {
      setError("No se pudo iniciar el nuevo chat.");
      setCreating(false);
    }
  }

  function beginRename(conversation: AiConversation) {
    setMenuId(null);
    setEditingId(conversation.id);
    setEditingTitle(conversation.title);
  }

  async function saveRename(conversationId: string) {
    const title = editingTitle.trim();
    if (!title) return;
    try {
      const updated = await phase1Service.updateConversation(projectId, conversationId, title);
      setConversations((items) =>
        items.map((item) => (item.id === updated.id ? updated : item))
      );
      setEditingId(null);
    } catch {
      setError("No se pudo cambiar el nombre del chat.");
    }
  }

  if (loading) {
    return (
      <section className="grid min-h-72 place-items-center" aria-live="polite">
        <div className="text-center">
          <LoaderCircle className="mx-auto animate-spin text-teal-700" size={32} />
          <p className="mt-3 text-sm font-semibold text-slate-600 dark:text-slate-300">Cargando chats...</p>
        </div>
      </section>
    );
  }

  if (error && !diagramId) {
    return (
      <section className="mx-auto grid min-h-72 max-w-xl place-items-center border border-rose-200 bg-white p-8 text-center dark:border-rose-900 dark:bg-slate-950">
        <div>
          <AlertCircle className="mx-auto text-rose-600" size={34} />
          <h1 className="mt-3 text-xl font-bold">No se pudo abrir Colaborativo</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{error}</p>
          <Link className="mt-5 inline-flex h-10 items-center border border-slate-300 px-4 text-sm font-semibold" to="/proyectos">Volver a proyectos</Link>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto w-full max-w-4xl">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">{projectName}</p>
          <h1 className="mt-1 text-2xl font-bold text-ink dark:text-white">Chats del proyecto</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Selecciona una conversacion para trabajar sobre el diagrama.</p>
        </div>
        <button
          className="inline-flex h-11 items-center gap-2 rounded-md bg-teal-700 px-4 text-sm font-bold text-white hover:bg-teal-800 disabled:opacity-60"
          disabled={creating}
          onClick={() => void createConversation()}
          type="button"
        >
          {creating ? <LoaderCircle className="animate-spin" size={18} /> : <Plus size={18} />}
          Nuevo chat
        </button>
      </header>

      {error && <p className="mt-4 border-l-4 border-rose-500 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:bg-rose-950/30 dark:text-rose-200">{error}</p>}

      <div className="mt-5 overflow-visible border-y border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="border-b border-slate-200 px-4 py-3 text-xs font-bold uppercase text-slate-500 dark:border-slate-800">Recientes</div>
        {conversations.map((conversation) => (
          <div className="relative flex min-h-16 items-center gap-3 border-b border-slate-100 px-4 transition last:border-b-0 hover:bg-teal-50/60 dark:border-slate-800 dark:hover:bg-slate-900" key={conversation.id}>
            <MessageSquare className="shrink-0 text-teal-700 dark:text-teal-300" size={19} />
            {editingId === conversation.id ? (
              <input
                autoFocus
                className="h-10 min-w-0 flex-1 rounded-md border border-teal-500 bg-white px-3 text-sm outline-none dark:bg-slate-900"
                maxLength={160}
                onBlur={() => void saveRename(conversation.id)}
                onChange={(event) => setEditingTitle(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") void saveRename(conversation.id);
                  if (event.key === "Escape") setEditingId(null);
                }}
                value={editingTitle}
              />
            ) : (
              <button className="min-w-0 flex-1 py-3 text-left" onClick={() => openConversation(conversation.id)} type="button">
                <span className="block truncate text-sm font-semibold text-slate-900 dark:text-white">{conversation.title}</span>
                <span className="mt-1 block text-xs text-slate-500">{new Date(conversation.updated_at).toLocaleString()}</span>
              </button>
            )}
            <div ref={menuId === conversation.id ? menuRef : undefined}>
              <button
                aria-expanded={menuId === conversation.id}
                aria-label={`Opciones de ${conversation.title}`}
                className={cn("grid size-9 place-items-center rounded-md text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800", menuId === conversation.id && "bg-slate-200 dark:bg-slate-800")}
                onClick={() => setMenuId((current) => current === conversation.id ? null : conversation.id)}
                title="Opciones del chat"
                type="button"
              >
                <MoreHorizontal size={19} />
              </button>
              {menuId === conversation.id && (
                <div className="absolute right-4 top-12 z-20 min-w-40 border border-slate-200 bg-white p-1 shadow-lg dark:border-slate-700 dark:bg-slate-900">
                  <button className="flex h-9 w-full items-center gap-2 rounded-sm px-3 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => beginRename(conversation)} type="button">
                    <Pencil size={15} />
                    Editar nombre
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
