import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bot,
  Check,
  ChevronUp,
  Circle,
  LoaderCircle,
  MessageSquarePlus,
  MessagesSquare,
  Mic,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { phase1Service } from "../../../core/api/phase1Service";
import type { AiProvider } from "../../../core/contracts/mejoras2p";
import type {
  AiAction,
  AiConversation,
  AiMessage,
  AiProviderHealth,
  AiRecommendation,
  ProjectPresence,
  ProjectSocketEventV2,
} from "../../../core/contracts/phase1";
import { useAuthStore } from "../../../core/auth/authStore";
import { useProjectPermissions } from "../../../core/permissions/useProjectPermissions";
import { useThemeStore } from "../../../core/theme/themeStore";
import { useSpeechRecognition } from "../../../core/voice/useSpeechRecognition";
import { ProjectSocketClient, type ParsedProjectSocketEvent } from "../../../core/websocket/projectSocket";
import { Avatar } from "../../../shared/components/Avatar";
import { cn } from "../../../shared/utils/cn";
import { projectService } from "../services/projectService";
import { useProjectAiStore } from "../store/projectAiStore";
import { AiProviderSettings } from "./AiProviderSettings";

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

export function ProjectAiAssistant({
  projectId,
  diagramId,
  initialConversationId,
  mode = "floating",
}: Props) {
  const navigate = useNavigate();
  const embedded = mode === "embedded";
  const dark = useThemeStore((state) => state.mode === "dark");
  const currentUser = useAuthStore((state) => state.user);
  const store = useProjectAiStore();
  const { can } = useProjectPermissions(projectId);

  const [open, setOpen] = useState(embedded);
  const [, setConversations] = useState<AiConversation[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [autoSend, setAutoSend] = useState(true);
  const [loading, setLoading] = useState(false);
  const [pendingRequest, setPendingRequest] = useState<{ id: string; content: string; label: string } | null>(null);
  const [busyActionId, setBusyActionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Proveedor de IA y salud
  const [currentProvider, setCurrentProvider] = useState<AiProvider>("ollama");
  const [providerHealth, setProviderHealth] = useState<AiProviderHealth | null>(null);
  const [providerSettingsOpen, setProviderSettingsOpen] = useState(false);
  const [voiceMessageIds, setVoiceMessageIds] = useState<Set<string>>(() => new Set());

  const endRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<ProjectSocketClient | null>(null);

  const catchUp = useCallback(async () => {
    if (!conversationId) return;
    const state = useProjectAiStore.getState();
    const page = await phase1Service.messages(projectId, {
      conversation_id: conversationId,
      after_sequence: state.conversationSequence,
      limit: 100,
    });
    page.items.forEach(state.upsertMessage);
    const [actions, recommendations, changes] = await Promise.all([
      phase1Service.actions(projectId, { conversation_id: conversationId, limit: 100 }),
      phase1Service.recommendations(projectId, { conversation_id: conversationId, limit: 100 }),
      projectService.changes(projectId, 200, state.projectSequence),
    ]);
    state.setActions(actions);
    state.setRecommendations(recommendations);
    state.setSequences(Math.max(state.projectSequence, ...changes.map((item) => item.sequence_number)));
  }, [conversationId, projectId]);

  const handleEvent = useCallback(
    (event: ParsedProjectSocketEvent) => {
      const state = useProjectAiStore.getState();
      if (!isV2(event)) {
        if (event.type === "SESSION_CONNECTED") {
          const session = event as typeof event & { project_sequence?: number };
          state.setSequences(session.project_sequence, undefined);
        }
        return;
      }
      const payloadConversationId =
        isRecord(event.payload) && typeof event.payload.conversation_id === "string"
          ? event.payload.conversation_id
          : null;
      const belongsToActiveChat = !payloadConversationId || payloadConversationId === conversationId;
      state.setSequences(
        event.sequence_number,
        belongsToActiveChat ? event.conversation_sequence ?? undefined : undefined
      );
      if (event.type === "SYNC_REQUIRED") {
        void catchUp().catch(() => setError("No se pudo sincronizar el historial."));
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_MESSAGE_CREATED" || event.type === "AI_MESSAGE_STATUS_CHANGED") &&
        isRecord(event.payload)
      ) {
        state.upsertMessage(event.payload as AiMessage);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_ACTION_PROPOSED" || event.type === "AI_ACTION_STATUS_CHANGED") &&
        isRecord(event.payload)
      ) {
        state.upsertAction(event.payload as AiAction);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_RECOMMENDATION_CREATED" || event.type === "AI_RECOMMENDATION_STATUS_CHANGED") &&
        isRecord(event.payload)
      ) {
        state.upsertRecommendation(event.payload as AiRecommendation);
      } else if (event.type === "PRESENCE_SNAPSHOT" && Array.isArray(event.payload.members)) {
        state.setPresence(event.payload.members as ProjectPresence[]);
      } else if (event.type === "PRESENCE_JOINED" && isRecord(event.payload.member)) {
        state.upsertPresence(event.payload.member as ProjectPresence);
      } else if (event.type === "PRESENCE_LEFT" && typeof event.payload.user_id === "string") {
        state.removePresence(event.payload.user_id);
      } else if (belongsToActiveChat && event.type === "AI_PROCESSING_STARTED") {
        state.setProcessing(true);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_PROCESSING_FINISHED" || event.type === "AI_PROCESSING_FAILED")
      ) {
        state.setProcessing(false);
      }
    },
    [catchUp, conversationId]
  );

  // Carga inicial de ajustes de IA y salud del proveedor
  useEffect(() => {
    phase1Service
      .aiSettings(projectId)
      .then((settings) => {
        if (settings?.preferred_provider) {
          setCurrentProvider(settings.preferred_provider);
        }
      })
      .catch(() => {});

    phase1Service
      .aiProviderHealth(projectId)
      .then((h) => setProviderHealth(h))
      .catch(() => setProviderHealth(null));
  }, [projectId]);

  useEffect(() => {
    setLoading(true);
    phase1Service
      .conversations(projectId)
      .then((items) => {
        setConversations(items);
        const saved = localStorage.getItem(`case-ai-chat:${projectId}`);
        const selected =
          items.find((item) => item.id === initialConversationId) ??
          items.find((item) => item.id === saved) ??
          items[0];
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
      phase1Service.recommendations(projectId, { conversation_id: conversationId, limit: 100 }),
    ])
      .then(([page, actions, recommendations]) => {
        state.setHistory(page.items, page.has_more_before);
        state.setActions(actions);
        state.setRecommendations(recommendations);
      })
      .catch(() => setError("No se pudo cargar el asistente del proyecto."))
      .finally(() => setLoading(false));

    const client = new ProjectSocketClient({
      projectId,
      getProjectSequence: () => useProjectAiStore.getState().projectSequence,
      getConversationSequence: () => useProjectAiStore.getState().conversationSequence,
      onEvent: handleEvent,
      onStatus: state.setSocketStatus,
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
        navigate(`/proyectos/${projectId}/uml/${diagramId}?panel=assistant&chat=${created.id}`, {
          replace: true,
        });
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
    store.actions.forEach((action) =>
      map.set(action.source_message_id, [...(map.get(action.source_message_id) ?? []), action])
    );
    return map;
  }, [store.actions]);

  const submit = async (
    content: string,
    label: string,
    restoreDraft = false,
    isVoice = false
  ) => {
    if (!content || loading || !conversationId) return;
    const clientMessageId = crypto.randomUUID();
    if (isVoice) {
      setVoiceMessageIds((prev) => new Set(prev).add(clientMessageId));
    }
    setError(null);
    setLoading(true);
    setPendingRequest({ id: clientMessageId, content, label });
    try {
      const response = await phase1Service.interact(projectId, {
        client_message_id: clientMessageId,
        conversation_id: conversationId,
        content,
        diagram_id: diagramId ?? null,
        requested_context: { include_diagram: true, include_recent_messages: true },
      });
      response.actions.forEach(store.upsertAction);
      response.recommendations.forEach(store.upsertRecommendation);
      await catchUp();
      setConversations(await phase1Service.conversations(projectId));
    } catch {
      if (restoreDraft) setDraft(content);
      setError(
        restoreDraft
          ? "No se pudo enviar. Tu texto se conservó para reintentar."
          : "No se pudo preparar la corrección. La recomendación sigue abierta."
      );
    } finally {
      setLoading(false);
      setPendingRequest(null);
    }
  };

  const send = async () => {
    const content = draft.trim();
    if (!content || loading) return;
    setDraft("");
    await submit(content, "El asistente está analizando el diagrama...", true, false);
  };

  // Reconocimiento de voz (useSpeechRecognition)
  const handleFinalSpeech = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      if (autoSend) {
        setDraft("");
        void submit(text.trim(), "El asistente está analizando el dictado por voz...", false, true);
      } else {
        setDraft((prev) => (prev.trim() ? `${prev.trim()} ${text.trim()}` : text.trim()));
      }
    },
    [autoSend, conversationId, diagramId, loading, projectId]
  );

  const speech = useSpeechRecognition({
    lang: "es-ES",
    onFinal: handleFinalSpeech,
  });

  const prepareRecommendation = async (recommendation: AiRecommendation) => {
    await submit(
      `Corrige el diagrama aplicando esta recomendación: ${recommendation.title}. ${recommendation.description}`,
      `Preparando la corrección: ${recommendation.title}...`
    );
  };

  const loadOlder = async () => {
    const first = store.messages[0]?.sequence_number;
    if (!first) return;
    if (!conversationId) return;
    const page = await phase1Service.messages(projectId, {
      conversation_id: conversationId,
      before_sequence: first,
      limit: 50,
    });
    store.prependHistory(page.items, page.has_more_before);
  };

  const decideAction = async (action: AiAction, decision: "confirm" | "reject") => {
    setBusyActionId(action.id);
    setError(null);
    try {
      const result =
        decision === "confirm"
          ? await phase1Service.confirmAiAction(projectId, action.id)
          : await phase1Service.rejectAiAction(projectId, action.id);
      store.upsertAction(result.action);
    } catch {
      setError("La acción cambió o no tienes permiso para ejecutarla.");
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
      const updated = await phase1Service.updateRecommendation(projectId, recommendation.id, {
        status,
      });
      store.upsertRecommendation(updated);
    } catch {
      setError("La recomendación cambió o ya fue resuelta.");
      await catchUp();
    }
  };

  const providerLabel = useMemo(() => {
    if (currentProvider === "gemini") return "Gemini · AI Studio";
    if (currentProvider === "rule_engine") return "Motor de reglas";
    return providerHealth?.selected_model
      ? `Ollama · ${providerHealth.selected_model.split(":")[0]}`
      : "Ollama · local";
  }, [currentProvider, providerHealth]);

  const canEditAiSettings = can("ai.settings");
  const canConfirmActions = can("ai.confirm_actions");
  const canChat = can("ai.chat");

  return (
    <div className={embedded ? "h-full min-h-0" : "fixed bottom-5 right-24 z-[65]"}>
      {open && (
        <section
          className={cn(
            "flex flex-col overflow-hidden",
            embedded
              ? "h-full min-h-0 w-full"
              : "mb-3 h-[min(680px,calc(100vh-120px))] w-[min(480px,calc(100vw-32px))] rounded-xl border shadow-2xl",
            dark ? "border-slate-800 bg-[#0b1424] text-slate-100" : "border-slate-200 bg-white text-slate-900"
          )}
          aria-label="Asistente del proyecto"
        >
          {/* Cabecera con selector de proveedor y presencia (maqueta.html#asistente) */}
          <header
            className={cn(
              "grid shrink-0 gap-2 border-b px-4 py-3 relative",
              dark ? "border-slate-800" : "border-slate-200"
            )}
          >
            <div className="flex min-w-0 items-center justify-between gap-2">
              <div className="flex min-w-0 items-center gap-2.5">
                <Avatar name="Asistente CASE" kind="ai" size="md" />
                <div className="min-w-0">
                  <h2 className="truncate text-sm font-bold text-slate-900 dark:text-slate-100">
                    Asistente del proyecto
                  </h2>
                  <p className="flex items-center gap-1.5 text-[11px] text-slate-500">
                    <Circle
                      className={
                        store.socketStatus === "connected"
                          ? "fill-emerald-500 text-emerald-500"
                          : "fill-amber-500 text-amber-500"
                      }
                      size={8}
                    />
                    {store.socketStatus === "connected"
                      ? `${store.presence.length || 1} en línea`
                      : "Reconectando"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {/* Píldora del proveedor */}
                <button
                  type="button"
                  id="prov-btn"
                  onClick={() => {
                    if (canEditAiSettings) setProviderSettingsOpen((v) => !v);
                  }}
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition",
                    dark
                      ? "border-slate-700 bg-slate-800/80 text-slate-300"
                      : "border-slate-200 bg-slate-100 text-slate-700",
                    canEditAiSettings ? "cursor-pointer hover:border-teal-500" : "cursor-default"
                  )}
                  title={canEditAiSettings ? "Cambiar proveedor de IA" : "Proveedor actual"}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      providerHealth?.available ? "bg-emerald-500" : "bg-amber-500"
                    )}
                  />
                  <span id="prov-name">{providerLabel}</span>
                </button>

                {/* Engranaje de ajustes de IA: solo con permiso ai.settings */}
                {canEditAiSettings && (
                  <AiProviderSettings
                    projectId={projectId}
                    current={currentProvider}
                    onChange={(p) => {
                      setCurrentProvider(p);
                      phase1Service
                        .aiProviderHealth(projectId)
                        .then((h) => setProviderHealth(h))
                        .catch(() => {});
                    }}
                    isOpen={providerSettingsOpen}
                    onClose={() => setProviderSettingsOpen(false)}
                  />
                )}

                {!embedded && (
                  <button
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md hover:bg-slate-100 dark:hover:bg-slate-800"
                    onClick={() => setOpen(false)}
                    title="Cerrar asistente"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>

            <div className="flex min-w-0 items-center gap-2">
              <button
                className={cn(
                  "flex h-8 min-w-0 flex-1 items-center justify-center gap-1.5 rounded-lg border px-3 text-xs font-semibold transition",
                  dark ? "border-slate-700 hover:bg-slate-800" : "border-slate-300 hover:bg-slate-50"
                )}
                onClick={() => navigate(`/proyectos/${projectId}/colaborativo`)}
                type="button"
              >
                <MessagesSquare size={14} />
                Ver chats del proyecto
              </button>
              <button
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-teal-700 hover:bg-teal-50 dark:text-teal-300 dark:hover:bg-slate-800"
                disabled={loading}
                onClick={() => void createConversation()}
                title="Nuevo chat"
                type="button"
              >
                <MessageSquarePlus size={16} />
              </button>
            </div>
          </header>

          {/* Historial de mensajes */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3.5" aria-live="polite">
            {store.hasMoreBefore && (
              <button
                className="mx-auto mb-2 flex items-center gap-1 text-xs font-semibold text-teal-600 hover:underline"
                onClick={() => void loadOlder()}
              >
                <ChevronUp size={14} />
                Cargar mensajes anteriores
              </button>
            )}

            {!loading && store.messages.length === 0 && (
              <p className="mt-12 text-center text-sm text-slate-400">
                Consulta sobre este proyecto o solicita cambios al diagrama abierto.
              </p>
            )}

            {store.messages.map((message) => {
              const isMe =
                message.role === "user" &&
                (Boolean(message.author_user_id && message.author_user_id === currentUser?.id) ||
                  !message.author_user_id);
              const isAi = message.role === "assistant";
              const isProactive =
                isAi && message.metadata_json && message.metadata_json.kind === "proactive";
              const isVoice =
                Boolean(message.metadata_json?.voice_input) || voiceMessageIds.has(message.id);

              if (isProactive) {
                return (
                  <div
                    key={message.id}
                    className="rounded-xl border border-amber-300 bg-amber-50/80 p-3.5 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/25"
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <Sparkles className="text-amber-600 dark:text-amber-400" size={16} />
                      <b className="text-xs font-bold text-amber-950 dark:text-amber-200">
                        Sugerencia de la IA
                      </b>
                      <span className="rounded-full bg-amber-200/80 px-2 py-0.5 text-[10px] font-bold text-amber-900 dark:bg-amber-900/60 dark:text-amber-200">
                        Proactiva
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap text-xs text-amber-950/90 dark:text-amber-100/90 leading-5">
                      {message.content}
                    </div>
                  </div>
                );
              }

              return (
                <article
                  key={message.id}
                  className={cn(
                    "flex flex-col max-w-[85%]",
                    isMe ? "ml-auto items-end" : "mr-auto items-start"
                  )}
                >
                  <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold text-slate-500">
                    {!isMe && (
                      <Avatar
                        name={message.author_display_name ?? (isAi ? "Asistente CASE" : "Integrante")}
                        userId={message.author_user_id ?? undefined}
                        kind={isAi ? "ai" : "user"}
                        size="sm"
                      />
                    )}
                    <span>
                      {isMe
                        ? "Tú"
                        : message.author_display_name ?? (isAi ? "Asistente CASE" : "Integrante")}
                    </span>
                  </div>

                  <div
                    className={cn(
                      "whitespace-pre-wrap rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm",
                      isMe
                        ? "bg-teal-600 text-white rounded-br-sm"
                        : dark
                        ? "bg-slate-800 text-slate-100 rounded-bl-sm"
                        : "bg-slate-100 text-slate-900 rounded-bl-sm"
                    )}
                  >
                    {message.content}

                    {isVoice && (
                      <span
                        className={cn(
                          "mt-1.5 flex items-center gap-1 text-[11px] font-semibold",
                          isMe ? "text-teal-100" : "text-teal-600 dark:text-teal-400"
                        )}
                      >
                        <Mic size={12} />
                        Dictado por voz
                      </span>
                    )}
                  </div>

                  {/* Acciones propuestas en este mensaje */}
                  {(actionsByMessage.get(message.id) ?? []).map((action) => (
                    <div
                      key={action.id}
                      className={cn(
                        "mt-2 w-full rounded-xl border p-3 text-xs shadow-sm",
                        action.status === "proposed"
                          ? "border-amber-300 bg-amber-50/70 text-amber-950 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-100"
                          : "border-teal-300 bg-teal-50/70 dark:border-teal-800 dark:bg-teal-950/20"
                      )}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="rounded bg-teal-100 px-1.5 py-0.5 text-[10px] font-bold text-teal-800 dark:bg-teal-900 dark:text-teal-200">
                          {action.action_type.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] uppercase font-bold tracking-wider opacity-75">
                          {action.status === "proposed" ? "Propuesta" : action.status}
                        </span>
                      </div>

                      {action.status === "proposed" && (
                        <div className="mt-2.5">
                          {canConfirmActions ? (
                            <div className="flex gap-2">
                              <button
                                disabled={busyActionId === action.id}
                                className="inline-flex h-7 items-center gap-1 rounded-md bg-teal-700 px-2.5 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-60"
                                onClick={() => void decideAction(action, "confirm")}
                              >
                                {busyActionId === action.id ? (
                                  <LoaderCircle className="animate-spin" size={12} />
                                ) : (
                                  <Check size={12} />
                                )}
                                Confirmar cambio
                              </button>
                              <button
                                disabled={busyActionId === action.id}
                                className="inline-flex h-7 items-center gap-1 rounded-md border border-slate-300 bg-white px-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 disabled:opacity-60"
                                onClick={() => void decideAction(action, "reject")}
                              >
                                <X size={12} />
                                Rechazar
                              </button>
                            </div>
                          ) : (
                            <p className="text-[11px] italic text-slate-500">
                              Solo Organizador y Editor pueden confirmar cambios.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </article>
              );
            })}

            {pendingRequest &&
              !store.messages.some((m) => m.client_message_id === pendingRequest.id) && (
                <article className="ml-auto max-w-[85%] flex flex-col items-end">
                  <span className="mb-1 text-[11px] font-semibold text-slate-500">Tú</span>
                  <div className="rounded-2xl rounded-br-sm bg-teal-600 px-3.5 py-2.5 text-sm text-white">
                    {pendingRequest.content}
                  </div>
                </article>
              )}

            {(store.processing || loading) && (
              <div className="flex items-center gap-2 text-xs text-slate-500 py-1" role="status">
                <LoaderCircle className="animate-spin text-teal-600" size={15} />
                <span>{pendingRequest?.label ?? "El asistente está procesando..."}</span>
              </div>
            )}

            {store.recommendations
              .filter((item) => item.status === "open")
              .map((item) => (
                <aside
                  key={item.id}
                  className={cn(
                    "rounded-xl border p-3 text-xs shadow-sm",
                    item.severity === "critical"
                      ? "border-red-300 bg-red-50 text-red-950 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-100"
                      : "border-sky-300 bg-sky-50 text-sky-950 dark:border-sky-900/50 dark:bg-sky-950/20 dark:text-sky-100"
                  )}
                >
                  <p className="font-bold">{item.title}</p>
                  <p className="mt-1 leading-5 opacity-80">{item.description}</p>
                  <div className="mt-2.5 flex gap-2">
                    <button
                      disabled={loading}
                      className="h-7 rounded-md bg-teal-700 px-2.5 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-60"
                      onClick={() => void prepareRecommendation(item)}
                    >
                      {loading ? "Procesando..." : "Preparar corrección"}
                    </button>
                    <button
                      className="h-7 rounded-md border border-current px-2.5 text-xs font-bold"
                      onClick={() => void decideRecommendation(item, "dismissed")}
                    >
                      Descartar
                    </button>
                  </div>
                </aside>
              ))}

            <div ref={endRef} />
          </div>

          {error && (
            <p className="border-t border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
              {error}
            </p>
          )}

          {speech.error && (
            <p className="border-t border-amber-200 bg-amber-50 px-4 py-1.5 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
              {speech.error}
            </p>
          )}

          {/* Compositor con soporte de voz (maqueta.html#asistente) */}
          <footer
            className={cn("shrink-0 border-t p-3", dark ? "border-slate-800" : "border-slate-200")}
          >
            {speech.listening && speech.interim && (
              <div
                className="mb-2 text-xs italic text-slate-500 bg-slate-50 dark:bg-slate-900/60 p-2 rounded-lg border border-dashed border-teal-400"
                aria-live="polite"
              >
                Dictando: {speech.interim}
              </div>
            )}

            <div className="flex items-end gap-2">
              <label htmlFor="draft" className="sr-only">
                Mensaje para el asistente
              </label>
              <textarea
                id="draft"
                value={draft}
                disabled={!canChat}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void send();
                  }
                }}
                rows={2}
                maxLength={20000}
                placeholder={
                  canChat
                    ? "Pregunta o pide un cambio. También puedes dictarlo."
                    : "No tienes permiso para interactuar en el chat (rol Lector)."
                }
                className={cn(
                  "min-h-12 flex-1 resize-none rounded-xl border px-3 py-2 text-sm outline-none transition focus:border-teal-500",
                  dark ? "border-slate-700 bg-slate-900" : "border-slate-300 bg-white",
                  !canChat && "opacity-50 cursor-not-allowed"
                )}
              />

              {/* Botón de micrófono: se renderiza solo si el navegador soporta SpeechRecognition */}
              {speech.supported && canChat && (
                <button
                  type="button"
                  id="mic"
                  aria-pressed={speech.listening}
                  aria-label="Dictar por voz"
                  title={speech.listening ? "Detener dictado" : "Dictar por voz"}
                  onClick={() => {
                    if (speech.listening) {
                      speech.stop();
                    } else {
                      speech.start();
                    }
                  }}
                  className={cn(
                    "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition shadow-sm",
                    speech.listening
                      ? "border-rose-500 bg-rose-600 text-white animate-pulse"
                      : dark
                      ? "border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
                      : "border-slate-300 bg-slate-100 text-slate-700 hover:bg-slate-200"
                  )}
                >
                  <Mic size={18} />
                </button>
              )}

              <button
                type="button"
                id="send"
                aria-label="Enviar"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-40"
                disabled={!draft.trim() || loading || !conversationId || !canChat}
                onClick={() => void send()}
                title="Enviar mensaje"
              >
                <Send size={18} />
              </button>
            </div>

            {/* Opciones del compositor */}
            {speech.supported && canChat && (
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                <label className="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    id="auto-send"
                    checked={autoSend}
                    onChange={(e) => setAutoSend(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Enviar al terminar de dictar</span>
                </label>
                <span>Chrome y Edge · español</span>
              </div>
            )}
          </footer>
        </section>
      )}

      {!embedded && (
        <button
          className="ml-auto flex h-14 w-14 items-center justify-center rounded-full bg-teal-600 text-white shadow-xl transition hover:bg-teal-700"
          onClick={() => setOpen((value) => !value)}
          title="Abrir asistente del proyecto"
          aria-expanded={open}
        >
          <Bot size={24} />
        </button>
      )}
    </div>
  );
}
