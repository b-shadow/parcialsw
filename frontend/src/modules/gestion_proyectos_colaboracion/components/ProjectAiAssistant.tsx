import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bot, Check, ChevronUp, Circle, LoaderCircle, MessagesSquare, MessageSquarePlus, Send, Sparkles, X } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { phase1Service } from "../../../core/api/phase1Service";
import type { AiAction, AiConversation, AiMessage, AiRecommendation, ProjectPresence, ProjectSocketEventV2 } from "../../../core/contracts/phase1";
import { ProjectSocketClient, type ParsedProjectSocketEvent } from "../../../core/websocket/projectSocket";
import { useThemeStore } from "../../../core/theme/themeStore";
import { cn } from "../../../shared/utils/cn";
import { useProjectAiStore } from "../store/projectAiStore";
import { projectService } from "../services/projectService";

type Props = {
  projectId: string;
  diagramId?: string | null;
  initialConversationId?: string | null;
  mode?: "floating" | "embedded";
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isV2(event: ParsedProjectSocketEvent): event is ProjectSocketEventV2 {
  return "protocol_version" in event && event.protocol_version === 2;
}

export function ProjectAiAssistant({ projectId, diagramId, initialConversationId, mode = "floating" }: Props) {
  const navigate = useNavigate();
  const embedded = mode === "embedded";
  const dark = useThemeStore((state) => state.mode === "dark");
  const store = useProjectAiStore();
  const [open, setOpen] = useState(embedded);
  const [, setConversations] = useState<AiConversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingRequest, setPendingRequest] = useState<{ id: string; content: string; label: string } | null>(null);
  const [busyActionId, setBusyActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<ProjectSocketClient | null>(null);

  const catchUp = useCallback(async () => {
    if (!conversationId) return;
    const state = useProjectAiStore.getState();
    const page = await phase1Service.messages(projectId, {
      conversation_id: conversationId,
      after_sequence: state.conversationSequence,
      limit: 100
    });
    page.items.forEach(state.upsertMessage);
    const [actions, recommendations, changes] = await Promise.all([
      phase1Service.actions(projectId, { conversation_id: conversationId, limit: 100 }),
      phase1Service.recommendations(projectId, { conversation_id: conversationId, limit: 100 }),
      projectService.changes(projectId, 200, state.projectSequence)
    ]);
    state.setActions(actions);
    state.setRecommendations(recommendations);
    state.setSequences(Math.max(state.projectSequence, ...changes.map((item) => item.sequence_number)));
  }, [conversationId, projectId]);

  const handleEvent = useCallback((event: ParsedProjectSocketEvent) => {
    const state = useProjectAiStore.getState();
    if (!isV2(event)) {
      if (event.type === "SESSION_CONNECTED") {
        const session = event as typeof event & { project_sequence?: number };
        state.setSequences(session.project_sequence, undefined);
      }
      return;
    }
    const payloadConversationId = isRecord(event.payload) && typeof event.payload.conversation_id === "string"
      ? event.payload.conversation_id
      : null;
    const belongsToActiveChat = !payloadConversationId || payloadConversationId === conversationId;
    state.setSequences(
      event.sequence_number,
      belongsToActiveChat ? event.conversation_sequence ?? undefined : undefined
    );
    if (event.type === "SYNC_REQUIRED") {
      void catchUp().catch(() => setError("No se pudo sincronizar el historial."));
    } else if (belongsToActiveChat && (event.type === "AI_MESSAGE_CREATED" || event.type === "AI_MESSAGE_STATUS_CHANGED") && isRecord(event.payload)) {
      state.upsertMessage(event.payload as AiMessage);
    } else if (belongsToActiveChat && (event.type === "AI_ACTION_PROPOSED" || event.type === "AI_ACTION_STATUS_CHANGED") && isRecord(event.payload)) {
      state.upsertAction(event.payload as AiAction);
    } else if (belongsToActiveChat && (event.type === "AI_RECOMMENDATION_CREATED" || event.type === "AI_RECOMMENDATION_STATUS_CHANGED") && isRecord(event.payload)) {
      state.upsertRecommendation(event.payload as AiRecommendation);
    } else if (event.type === "PRESENCE_SNAPSHOT" && Array.isArray(event.payload.members)) {
      state.setPresence(event.payload.members as ProjectPresence[]);
    } else if (event.type === "PRESENCE_JOINED" && isRecord(event.payload.member)) {
      state.upsertPresence(event.payload.member as ProjectPresence);
    } else if (event.type === "PRESENCE_LEFT" && typeof event.payload.user_id === "string") {
      state.removePresence(event.payload.user_id);
    } else if (belongsToActiveChat && event.type === "AI_PROCESSING_STARTED") {
      state.setProcessing(true);
    } else if (belongsToActiveChat && (event.type === "AI_PROCESSING_FINISHED" || event.type === "AI_PROCESSING_FAILED")) {
      state.setProcessing(false);
    }
  }, [catchUp, conversationId]);

  useEffect(() => {
    setLoading(true);
    phase1Service.conversations(projectId)
      .then((items) => {
        setConversations(items);
        const saved = localStorage.getItem(`case-ai-chat:${projectId}`);
        const selected = items.find((item) => item.id === initialConversationId)
          ?? items.find((item) => item.id === saved)
          ?? items[0];
        setConversationId(selected?.id ?? null);
      })
      .catch(() => setError("No se pudieron cargar los chats del proyecto."))
      .finally(() => setLoading(false));
  }, [initialConversationId, projectId]);

  useEffect(() => {
    if (!conversationId) return;
    const state = useProjectAiStore.getState();
    state.initialize(projectId, conversationId);
    localStorage.setItem(`case-ai-chat:${projectId}`, conversationId);
    setDraft(localStorage.getItem(`case-ai-draft:${projectId}:${conversationId}`) ?? "");
    setLoading(true);
    Promise.all([
      phase1Service.messages(projectId, { conversation_id: conversationId, limit: 50 }),
      phase1Service.actions(projectId, { conversation_id: conversationId, limit: 100 }),
      phase1Service.recommendations(projectId, { conversation_id: conversationId, limit: 100 })
    ]).then(([page, actions, recommendations]) => {
      state.setHistory(page.items, page.has_more_before);
      state.setActions(actions);
      state.setRecommendations(recommendations);
    }).catch(() => setError("No se pudo cargar el asistente del proyecto."))
      .finally(() => setLoading(false));

    const client = new ProjectSocketClient({
      projectId,
      getProjectSequence: () => useProjectAiStore.getState().projectSequence,
      getConversationSequence: () => useProjectAiStore.getState().conversationSequence,
      onEvent: handleEvent,
      onStatus: state.setSocketStatus
    });
    clientRef.current = client;
    client.connect();
    return () => {
      client.close();
      clientRef.current = null;
    };
  }, [conversationId, handleEvent, projectId]);

  useEffect(() => {
    clientRef.current?.setActiveDiagram(diagramId ?? null);
  }, [diagramId]);

  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(`case-ai-draft:${projectId}:${conversationId}`, draft);
    }
  }, [conversationId, draft, projectId]);

  const createConversation = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const created = await phase1Service.createConversation(projectId);
      setConversations((items) => [created, ...items]);
      setConversationId(created.id);
      if (diagramId) {
        navigate(
          `/proyectos/${projectId}/uml/${diagramId}?panel=assistant&chat=${created.id}`,
          { replace: true }
        );
      }
    } catch {
      setError("No se pudo iniciar un nuevo chat.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [open, store.messages.length, store.processing]);

  const actionsByMessage = useMemo(() => {
    const map = new Map<string, AiAction[]>();
    store.actions.forEach((action) => map.set(action.source_message_id, [...(map.get(action.source_message_id) ?? []), action]));
    return map;
  }, [store.actions]);

  const submit = async (content: string, label: string, restoreDraft = false) => {
    if (!content || loading || !conversationId) return;
    const clientMessageId = crypto.randomUUID();
    setError(null);
    setLoading(true);
    setPendingRequest({ id: clientMessageId, content, label });
    try {
      const response = await phase1Service.interact(projectId, {
        client_message_id: clientMessageId,
        conversation_id: conversationId,
        content,
        diagram_id: diagramId ?? null,
        requested_context: { include_diagram: true, include_recent_messages: true }
      });
      response.actions.forEach(store.upsertAction);
      response.recommendations.forEach(store.upsertRecommendation);
      await catchUp();
      setConversations(await phase1Service.conversations(projectId));
    } catch {
      if (restoreDraft) setDraft(content);
      setError(restoreDraft
        ? "No se pudo enviar. Tu texto se conservo para reintentar."
        : "No se pudo preparar la correccion. La recomendacion sigue abierta.");
    } finally {
      setLoading(false);
      setPendingRequest(null);
    }
  };

  const send = async () => {
    const content = draft.trim();
    if (!content || loading) return;
    setDraft("");
    await submit(content, "El asistente esta analizando el diagrama...", true);
  };

  const prepareRecommendation = async (recommendation: AiRecommendation) => {
    await submit(
      `Corrige el diagrama aplicando esta recomendacion: ${recommendation.title}. ${recommendation.description}`,
      `Preparando la correccion: ${recommendation.title}...`
    );
  };

  const loadOlder = async () => {
    const first = store.messages[0]?.sequence_number;
    if (!first) return;
    if (!conversationId) return;
    const page = await phase1Service.messages(projectId, {
      conversation_id: conversationId,
      before_sequence: first,
      limit: 50
    });
    store.prependHistory(page.items, page.has_more_before);
  };

  const decideAction = async (action: AiAction, decision: "confirm" | "reject") => {
    setBusyActionId(action.id);
    setError(null);
    try {
      const result = decision === "confirm"
        ? await phase1Service.confirmAiAction(projectId, action.id)
        : await phase1Service.rejectAiAction(projectId, action.id);
      store.upsertAction(result.action);
    } catch {
      setError("La accion cambio o no tienes permiso para ejecutarla.");
      await catchUp();
    } finally {
      setBusyActionId(null);
    }
  };

  const decideRecommendation = async (
    recommendation: AiRecommendation,
    status: "accepted" | "dismissed" | "resolved"
  ) => {
    try {
      const updated = await phase1Service.updateRecommendation(
        projectId,
        recommendation.id,
        { status }
      );
      store.upsertRecommendation(updated);
    } catch {
      setError("La recomendacion cambio o ya fue resuelta.");
      await catchUp();
    }
  };

  return (
    <div className={embedded ? "h-full min-h-0" : "fixed bottom-5 right-24 z-[65]"}>
      {open && (
        <section className={cn(
          "flex flex-col overflow-hidden",
          embedded
            ? "h-full min-h-0 w-full"
            : "mb-3 h-[min(680px,calc(100vh-120px))] w-[min(430px,calc(100vw-32px))] rounded-lg border shadow-2xl",
          dark ? "border-slate-700 bg-[#0b1424] text-slate-100" : "border-slate-200 bg-white text-slate-900"
        )} aria-label="Asistente del proyecto">
          <header className={cn("grid shrink-0 gap-2 border-b px-4 py-3", dark ? "border-slate-700" : "border-slate-200")}>
            <div className="flex min-w-0 items-center justify-between gap-2">
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white"><Sparkles size={18} /></span>
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-bold">Asistente del proyecto</h2>
                  <p className="flex items-center gap-1 text-[11px] text-slate-500">
                    <Circle className={store.socketStatus === "connected" ? "fill-emerald-500 text-emerald-500" : "fill-amber-500 text-amber-500"} size={8} />
                    {store.socketStatus === "connected" ? `${store.presence.length || 1} en linea` : "Reconectando"}
                  </p>
                </div>
              </div>
              {!embedded && <button className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => setOpen(false)} title="Cerrar asistente"><X size={18} /></button>}
            </div>
            <div className="flex min-w-0 items-center gap-2">
              <button
                className={cn(
                  "flex h-9 min-w-0 flex-1 items-center justify-center gap-2 rounded-md border px-3 text-xs font-bold",
                  dark ? "border-slate-700 hover:bg-slate-800" : "border-slate-300 hover:bg-slate-50"
                )}
                onClick={() => navigate(`/proyectos/${projectId}/colaborativo`)}
                type="button"
              >
                <MessagesSquare size={16} />
                Ver chats
              </button>
              <button
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-slate-800"
                disabled={loading}
                onClick={() => void createConversation()}
                title="Nuevo chat"
                type="button"
              >
                <MessageSquarePlus size={18} />
              </button>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto px-4 py-3" aria-live="polite">
            {store.hasMoreBefore && <button className="mx-auto mb-3 flex items-center gap-1 text-xs font-semibold text-teal-600" onClick={() => void loadOlder()}><ChevronUp size={14} />Cargar anteriores</button>}
            {!loading && store.messages.length === 0 && <p className="mt-12 text-center text-sm text-slate-500">Consulta sobre este proyecto o solicita cambios al diagrama abierto.</p>}
            <div className="grid gap-3">
              {store.messages.map((message) => (
                <article key={message.id} className={cn("max-w-[88%]", message.role === "user" ? "ml-auto" : "mr-auto")}>
                  <p className="mb-1 text-[11px] font-semibold text-slate-500">{message.author_display_name ?? (message.role === "assistant" ? "Asistente CASE" : "Integrante")}</p>
                  <div className={cn("whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-5", message.role === "user" ? "bg-teal-600 text-white" : dark ? "bg-slate-800" : "bg-slate-100")}>{message.content}</div>
                  {(actionsByMessage.get(message.id) ?? []).map((action) => (
                    <div key={action.id} className={cn("mt-2 border-l-2 px-3 py-2 text-xs", action.status === "proposed" ? "border-amber-500 bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100" : "border-teal-500 bg-teal-50 dark:bg-teal-950/30")}>
                      <p className="font-bold">{action.action_type.replace(/_/g, " ")}</p>
                      <p className="mt-1 opacity-75">Estado: {action.status}</p>
                      {action.status === "proposed" && (
                        <div className="mt-2 flex gap-2">
                          <button disabled={busyActionId === action.id} className="inline-flex h-8 items-center gap-1 rounded-md bg-teal-700 px-3 font-bold text-white disabled:opacity-60" onClick={() => void decideAction(action, "confirm")}>{busyActionId === action.id ? <LoaderCircle className="animate-spin" size={14} /> : <Check size={14} />}{busyActionId === action.id ? "Aplicando..." : "Aplicar"}</button>
                          <button disabled={busyActionId === action.id} className="inline-flex h-8 items-center gap-1 rounded-md border border-current px-3 font-bold disabled:opacity-60" onClick={() => void decideAction(action, "reject")}><X size={14} />Rechazar</button>
                        </div>
                      )}
                    </div>
                  ))}
                </article>
              ))}
              {pendingRequest && !store.messages.some((message) => message.client_message_id === pendingRequest.id) && (
                <article className="ml-auto max-w-[88%]">
                  <p className="mb-1 text-[11px] font-semibold text-slate-500">Tu</p>
                  <div className="whitespace-pre-wrap rounded-lg bg-teal-600 px-3 py-2 text-sm leading-5 text-white">{pendingRequest.content}</div>
                </article>
              )}
              {(store.processing || loading) && <div className="flex items-center gap-2 text-xs text-slate-500" role="status"><LoaderCircle className="animate-spin" size={15} />{pendingRequest?.label ?? "El asistente esta procesando..."}</div>}
              {store.recommendations.filter((item) => item.status === "open").map((item) => (
                <aside key={item.id} className={cn(
                  "border-l-2 px-3 py-2 text-xs",
                  item.severity === "critical"
                    ? "border-red-500 bg-red-50 text-red-950 dark:bg-red-950/30 dark:text-red-100"
                    : "border-sky-500 bg-sky-50 text-sky-950 dark:bg-sky-950/30 dark:text-sky-100"
                )}>
                  <p className="font-bold">{item.title}</p>
                  <p className="mt-1 leading-5 opacity-80">{item.description}</p>
                  <div className="mt-2 flex gap-2">
                    <button disabled={loading} className="h-8 rounded-md bg-teal-700 px-3 font-bold text-white disabled:opacity-60" onClick={() => void prepareRecommendation(item)}>{loading ? "Procesando..." : "Preparar correccion"}</button>
                    <button className="h-8 rounded-md border border-current px-3 font-bold" onClick={() => void decideRecommendation(item, "dismissed")}>Descartar</button>
                  </div>
                </aside>
              ))}
              <div ref={endRef} />
            </div>
          </div>

          {error && <p className="border-t border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">{error}</p>}
          <footer className={cn("shrink-0 border-t p-3", dark ? "border-slate-700" : "border-slate-200")}>
            <div className="flex items-end gap-2">
              <textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} rows={2} maxLength={20000} placeholder="Pregunta o solicita un cambio..." className={cn("min-h-12 flex-1 resize-none rounded-lg border px-3 py-2 text-sm outline-none focus:border-teal-500", dark ? "border-slate-700 bg-slate-900" : "border-slate-300 bg-white")} />
              <button className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white disabled:opacity-40" disabled={!draft.trim() || loading || !conversationId} onClick={() => void send()} title="Enviar mensaje"><Send size={18} /></button>
            </div>
          </footer>
        </section>
      )}
      {!embedded && <button className="ml-auto flex h-14 w-14 items-center justify-center rounded-full bg-teal-600 text-white shadow-xl transition hover:bg-teal-700" onClick={() => setOpen((value) => !value)} title="Abrir asistente del proyecto" aria-expanded={open}><Bot size={24} /></button>}
    </div>
  );
}
