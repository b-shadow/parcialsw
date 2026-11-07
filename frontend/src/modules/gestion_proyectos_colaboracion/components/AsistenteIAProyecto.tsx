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

import { servicioFase1 } from "../../../core/api/servicioFase1";
import type { ProveedorIA } from "../../../core/contracts/mejoras2p";
import type {
  AccionIA,
  ConversacionIA,
  MensajeIA,
  EstadoProveedorIA,
  RecomendacionIA,
  PresenciaProyecto,
  EventoSocketProyectoV2,
} from "../../../core/contracts/phase1";
import { useAlmacenAutenticacion } from "../../../core/auth/almacenAutenticacion";
import { usePermisosProyecto } from "../../../core/permissions/usePermisosProyecto";
import { useAlmacenTema } from "../../../core/theme/almacenTema";
import { useReconocimientoVoz } from "../../../core/voice/useReconocimientoVoz";
import { ClienteSocketProyecto, type EventoSocketProyectoAnalizado } from "../../../core/websocket/socketProyecto";
import { Avatar } from "../../../shared/components/Avatar";
import { cn } from "../../../shared/utils/cn";
import { servicioProyectos } from "../services/servicioProyectos";
import { ultimaSecuenciaContinuaMensajes, useAlmacenIAProyecto } from "../store/almacenIAProyecto";
import { ConfiguracionProveedorIA } from "./ConfiguracionProveedorIA";
import { dependenciasAccionListas, resumenAccion } from "./resumenAccion";
import { preparacionRecomendacion, solicitudCorreccionConCriterio } from "./preparacionRecomendacion";

type Props = {
  projectId: string;
  diagramId?: string | null;
  initialConversationId?: string | null;
  mode?: "floating" | "embedded";
};

function esRegistro(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function esVersionDos(event: EventoSocketProyectoAnalizado): event is EventoSocketProyectoV2 {
  return "protocol_version" in event && event.protocol_version === 2;
}

export function AsistenteIAProyecto({
  projectId,
  diagramId,
  initialConversationId,
  mode = "floating",
}: Props) {
  const navigate = useNavigate();
  const embedded = mode === "embedded";
  const dark = useAlmacenTema((state) => state.mode === "dark");
  const currentUser = useAlmacenAutenticacion((state) => state.user);
  const store = useAlmacenIAProyecto();
  const { can } = usePermisosProyecto(projectId);

  const [open, setOpen] = useState(embedded);
  const [, setConversations] = useState<ConversacionIA[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [autoSend, setAutoSend] = useState(true);
  const [loading, setLoading] = useState(false);
  const [pendingRequest, setPendingRequest] = useState<{ id: string; content: string; label: string } | null>(null);
  const [busyActionId, setBusyActionId] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recommendationGuidance, setRecommendationGuidance] = useState<{
    id: string;
    text: string;
  } | null>(null);
  const [recommendationCriterion, setRecommendationCriterion] = useState("");

  // Proveedor de IA y salud
  const [currentProvider, setCurrentProvider] = useState<ProveedorIA>("ollama");
  const [currentSource, setCurrentSource] = useState<"local" | "aws">("local");
  const [providerHealth, setProviderHealth] = useState<EstadoProveedorIA | null>(null);
  const [providerSettingsOpen, setProviderSettingsOpen] = useState(false);
  const [voiceMessageIds, setVoiceMessageIds] = useState<Set<string>>(() => new Set());

  const endRef = useRef<HTMLDivElement>(null);
  const clientRef = useRef<ClienteSocketProyecto | null>(null);

  const ponerseAlDia = useCallback(async () => {
    if (!conversationId) return;
    const state = useAlmacenIAProyecto.getState();
    let cursor = ultimaSecuenciaContinuaMensajes(state.messages);
    for (let pageNumber = 0; pageNumber < 20; pageNumber += 1) {
      const page = await servicioFase1.listarMensajes(projectId, {
        conversation_id: conversationId,
        after_sequence: cursor,
        limit: 100,
      });
      if (useAlmacenIAProyecto.getState().conversationId !== conversationId) return;
      page.items.forEach(state.upsertMessage);
      const nextCursor = ultimaSecuenciaContinuaMensajes(useAlmacenIAProyecto.getState().messages);
      if (!page.has_more_after || nextCursor <= cursor) break;
      cursor = nextCursor;
    }
    const [actions, recommendations, changes] = await Promise.all([
      servicioFase1.listarAcciones(projectId, { conversation_id: conversationId, limit: 100 }),
      servicioFase1.listarRecomendaciones(projectId, { conversation_id: conversationId, limit: 100 }),
      servicioProyectos.listarCambios(projectId, 200, state.projectSequence),
    ]);
    if (useAlmacenIAProyecto.getState().conversationId !== conversationId) return;
    state.establecerAcciones(actions);
    state.establecerRecomendaciones(recommendations);
    state.establecerSecuencias(Math.max(state.projectSequence, ...changes.map((item) => item.sequence_number)));
  }, [conversationId, projectId]);

  const manejarEvento = useCallback(
    (event: EventoSocketProyectoAnalizado) => {
      const state = useAlmacenIAProyecto.getState();
      if (state.projectId !== projectId || state.conversationId !== conversationId) return;
      if (!esVersionDos(event)) {
        if (event.type === "SESSION_CONNECTED") {
          const session = event as typeof event & { project_sequence?: number };
          state.establecerSecuencias(session.project_sequence, undefined);
        }
        return;
      }
      const payloadConversationId =
        esRegistro(event.payload) && typeof event.payload.conversation_id === "string"
          ? event.payload.conversation_id
          : null;
      const belongsToActiveChat = !payloadConversationId || payloadConversationId === conversationId;
      state.establecerSecuencias(
        event.sequence_number
      );
      if (event.type === "SYNC_REQUIRED") {
        void ponerseAlDia().catch(() => setError("No se pudo sincronizar el historial."));
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_MESSAGE_CREATED" || event.type === "AI_MESSAGE_STATUS_CHANGED") &&
        esRegistro(event.payload)
      ) {
        state.upsertMessage(event.payload as MensajeIA);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_ACTION_PROPOSED" || event.type === "AI_ACTION_STATUS_CHANGED") &&
        esRegistro(event.payload)
      ) {
        state.upsertAction(event.payload as AccionIA);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_RECOMMENDATION_CREATED" || event.type === "AI_RECOMMENDATION_STATUS_CHANGED") &&
        esRegistro(event.payload)
      ) {
        state.upsertRecommendation(event.payload as RecomendacionIA);
      } else if (event.type === "PRESENCE_SNAPSHOT" && Array.isArray(event.payload.members)) {
        state.establecerPresencia(event.payload.members as PresenciaProyecto[]);
      } else if (event.type === "PRESENCE_JOINED" && esRegistro(event.payload.member)) {
        state.upsertPresence(event.payload.member as PresenciaProyecto);
      } else if (event.type === "PRESENCE_LEFT" && typeof event.payload.user_id === "string") {
        state.quitarPresencia(event.payload.user_id);
      } else if (belongsToActiveChat && event.type === "AI_PROCESSING_STARTED") {
        state.establecerProcesamiento(true);
      } else if (
        belongsToActiveChat &&
        (event.type === "AI_PROCESSING_FINISHED" || event.type === "AI_PROCESSING_FAILED")
      ) {
        state.establecerProcesamiento(false);
      }
    },
    [ponerseAlDia, conversationId, projectId]
  );

  // Carga inicial de ajustes de IA y salud del proveedor
  useEffect(() => {
    if (!open) return;
    let active = true;
    const recargar = () => {
      servicioFase1.configuracionIA(projectId).then((settings) => {
        if (!active) return;
        setCurrentProvider(settings.preferred_provider);
        setCurrentSource(settings.settings_json.origen_ollama === "aws" ? "aws" : "local");
      }).catch(() => {});
      servicioFase1.estadoProveedorIA(projectId).then((health) => {
        if (active) setProviderHealth(health);
      }).catch(() => {
        if (active) setProviderHealth(null);
      });
    };
    recargar();
    const timer = window.setInterval(recargar, 30_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [projectId, open]);

  useEffect(() => {
    setLoading(true);
    servicioFase1
      .listarConversaciones(projectId)
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
    let active = true;
    const state = useAlmacenIAProyecto.getState();
    state.initialize(projectId, conversationId);
    localStorage.setItem(`case-ai-chat:${projectId}`, conversationId);
    setDraft(localStorage.getItem(`case-ai-draft:${projectId}:${conversationId}`) ?? "");
    setLoading(true);
    Promise.all([
      servicioFase1.listarMensajes(projectId, { conversation_id: conversationId, limit: 50 }),
      servicioFase1.listarAcciones(projectId, { conversation_id: conversationId, limit: 100 }),
      servicioFase1.listarRecomendaciones(projectId, { conversation_id: conversationId, limit: 100 }),
    ])
      .then(([page, actions, recommendations]) => {
        if (!active || useAlmacenIAProyecto.getState().conversationId !== conversationId) return;
        state.establecerHistorial(page.items, page.has_more_before);
        state.establecerAcciones(actions);
        state.establecerRecomendaciones(recommendations);
      })
      .catch(() => { if (active) setError("No se pudo cargar el asistente del proyecto."); })
      .finally(() => { if (active) setLoading(false); });

    const client = new ClienteSocketProyecto({
      projectId,
      obtenerSecuenciaProyecto: () => useAlmacenIAProyecto.getState().projectSequence,
      obtenerSecuenciaConversacion: () => ultimaSecuenciaContinuaMensajes(useAlmacenIAProyecto.getState().messages),
      alRecibirEvento: manejarEvento,
      alCambiarEstado: state.establecerEstadoSocket,
    });
    clientRef.current = client;
    client.conectar();
    return () => {
      active = false;
      client.cerrar();
      clientRef.current = null;
    };
  }, [conversationId, manejarEvento, projectId]);

  useEffect(() => {
    clientRef.current?.establecerDiagramaActivo(diagramId ?? null);
  }, [diagramId]);

  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(`case-ai-draft:${projectId}:${conversationId}`, draft);
    }
  }, [conversationId, draft, projectId]);

  const crearConversacion = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const created = await servicioFase1.crearConversacion(projectId);
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
    const map = new Map<string, AccionIA[]>();
    store.actions.forEach((action) =>
      map.set(action.source_message_id, [...(map.get(action.source_message_id) ?? []), action])
    );
    return map;
  }, [store.actions]);

  const enviarSolicitud = async (
    content: string,
    label: string,
    restoreDraft = false,
    isVoice = false
  ) => {
    if (!content || loading || !conversationId) return false;
    const clientMessageId = crypto.randomUUID();
    if (isVoice) {
      setVoiceMessageIds((prev) => new Set(prev).add(clientMessageId));
    }
    setError(null);
    setLoading(true);
    setPendingRequest({ id: clientMessageId, content, label });
    let interactionCompleted = false;
    try {
      const response = await servicioFase1.interactuar(projectId, {
        client_message_id: clientMessageId,
        conversation_id: conversationId,
        content,
        diagram_id: diagramId ?? null,
        requested_context: { include_diagram: true, include_recent_messages: true },
      });
      interactionCompleted = true;
      response.actions.forEach(store.upsertAction);
      response.recommendations.forEach(store.upsertRecommendation);
      await ponerseAlDia();
      setConversations(await servicioFase1.listarConversaciones(projectId));
      return true;
    } catch {
      store.establecerProcesamiento(false);
      if (interactionCompleted) {
        setError("La respuesta se guardó, pero no se pudo sincronizar el historial. Recarga el chat.");
        return true;
      }
      let remoteStatus: "answered" | "pending" | "failed" | "unknown" = "unknown";
      try {
        const page = await servicioFase1.listarMensajes(projectId, {
          conversation_id: conversationId,
          limit: 50,
        });
        if (useAlmacenIAProyecto.getState().conversationId === conversationId) {
          store.establecerHistorial(page.items, page.has_more_before);
        }
        const submitted = page.items.find((item) => item.client_message_id === clientMessageId);
        if (submitted) {
          remoteStatus = page.items.some(
            (item) => item.role === "assistant" && item.correlation_id === submitted.correlation_id
          ) ? "answered" : submitted.status === "pending" ? "pending" : "failed";
        }
      } catch {
        // El borrador sigue disponible incluso si el historial no puede recargarse.
      }
      if (remoteStatus === "answered") {
        try { await ponerseAlDia(); } catch { /* El historial ya contiene la respuesta. */ }
        return true;
      }
      if (remoteStatus === "pending") {
        store.establecerProcesamiento(true);
        setError("El mensaje se guardó y el asistente sigue procesándolo.");
        return true;
      }
      if (restoreDraft) setDraft(content);
      setError(
        restoreDraft
          ? "No se pudo enviar. Tu texto se conservó para reintentar."
          : "No se pudo preparar la corrección. La recomendación sigue abierta."
      );
      return false;
    } finally {
      setLoading(false);
      setPendingRequest(null);
    }
  };

  const enviar = async () => {
    const content = draft.trim();
    if (!content || loading) return;
    setDraft("");
    await enviarSolicitud(content, "El asistente está analizando el diagrama...", true, false);
  };

  // Reconocimiento de voz (useSpeechRecognition)
  const manejarDictadoFinal = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      if (autoSend) {
        setDraft("");
        void enviarSolicitud(text.trim(), "El asistente está analizando el dictado por voz...", false, true);
      } else {
        setDraft((prev) => (prev.trim() ? `${prev.trim()} ${text.trim()}` : text.trim()));
      }
    },
    [autoSend, conversationId, diagramId, loading, projectId]
  );

  const speech = useReconocimientoVoz({
    lang: "es-ES",
    alFinalizar: manejarDictadoFinal,
  });

  const prepararRecomendacion = async (recommendation: RecomendacionIA) => {
    const preparation = preparacionRecomendacion(recommendation.title);
    if (preparation.kind === "manual") {
      setRecommendationGuidance({ id: recommendation.id, text: preparation.guidance });
      setRecommendationCriterion("");
      return;
    }
    setRecommendationGuidance(null);
    await enviarSolicitud(
      `Corrige el diagrama aplicando esta recomendación: ${recommendation.title}. ${recommendation.description}`,
      `Preparando la corrección: ${recommendation.title}...`
    );
  };

  const prepararConCriterio = async (recommendation: RecomendacionIA) => {
    if (!recommendationCriterion.trim()) return;
    const accepted = await enviarSolicitud(
      solicitudCorreccionConCriterio(
        recommendation.title,
        recommendation.description,
        recommendationCriterion
      ),
      `Preparando propuesta para ${recommendation.title}...`,
      false
    );
    if (accepted) {
      setRecommendationGuidance(null);
      setRecommendationCriterion("");
    }
  };

  const cargarAnteriores = async () => {
    const first = store.messages[0]?.sequence_number;
    if (!first) return;
    if (!conversationId) return;
    const page = await servicioFase1.listarMensajes(projectId, {
      conversation_id: conversationId,
      before_sequence: first,
      limit: 50,
    });
    store.prependHistory(page.items, page.has_more_before);
  };

  const decidirAccion = async (action: AccionIA, decision: "confirm" | "reject") => {
    setBusyActionId(action.id);
    setError(null);
    setActionFeedback(null);
    try {
      const result =
        decision === "confirm"
          ? await servicioFase1.confirmarAccionIA(projectId, action.id)
          : await servicioFase1.rechazarAccionIA(projectId, action.id);
      store.upsertAction(result.action);
      if (decision === "confirm") {
        setActionFeedback(result.action.status === "applied"
          ? "Cambio aplicado. El diagrama se está actualizando."
          : "La acción aún no se aplicó; revisa su estado.");
      }
    } catch {
      setError("La acción cambió o no tienes permiso para ejecutarla.");
      await ponerseAlDia();
    } finally {
      setBusyActionId(null);
    }
  };

  const decidirRecomendacion = async (
    recommendation: RecomendacionIA,
    status: "accepted" | "dismissed" | "resolved"
  ) => {
    try {
      const updated = await servicioFase1.actualizarRecomendacion(projectId, recommendation.id, {
        status,
      });
      store.upsertRecommendation(updated);
    } catch {
      setError("La recomendación cambió o ya fue resuelta.");
      await ponerseAlDia();
    }
  };

  const providerLabel = useMemo(() => {
    if (currentProvider === "gemini") return "Gemini · AI Studio";
    if (currentProvider === "rule_engine") return "Motor de reglas";
    return providerHealth?.selected_model
      ? `Ollama · ${providerHealth.selected_model.split(":")[0]}`
      : `Ollama · ${currentSource === "aws" ? "AWS" : "local"}`;
  }, [currentProvider, currentSource, providerHealth]);

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
                  title={canEditAiSettings ? "Proveedor configurado; pulsa para cambiarlo" : "Proveedor configurado"}
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
                  <ConfiguracionProveedorIA
                    projectId={projectId}
                    current={currentProvider}
                    currentSource={currentSource}
                    onSourceChange={setCurrentSource}
                    onChange={(p) => {
                      setCurrentProvider(p);
                      servicioFase1
                        .estadoProveedorIA(projectId)
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
                onClick={() => void crearConversacion()}
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
                onClick={() => void cargarAnteriores()}
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

                  {isMe && message.status === "failed" && (
                    <span className="mt-1 text-[11px] font-semibold text-red-600" role="status">
                      No se pudo procesar. Puedes volver a enviar la pregunta.
                    </span>
                  )}
                  {isAi && typeof message.metadata_json.provider === "string" && (
                    <span className="mt-1 text-[10px] text-slate-500">
                      Respondió: {message.metadata_json.provider === "rule_engine"
                        ? "Reglas locales"
                        : message.metadata_json.provider === "ollama"
                          ? "Ollama"
                          : message.metadata_json.provider}
                    </span>
                  )}

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
                          {resumenAccion(action).title}
                        </span>
                        <span className="text-[10px] uppercase font-bold tracking-wider opacity-75">
                          {action.status === "proposed" ? "Propuesta" : action.status}
                        </span>
                      </div>
                      <p className="mt-2 break-words text-[11px] leading-4">{resumenAccion(action).details}</p>
                      {action.status === "proposed" && (
                        <details className="mt-1 text-[11px]">
                          <summary className="cursor-pointer font-semibold">Ver datos del cambio</summary>
                          <pre className="mt-1 max-h-36 overflow-auto whitespace-pre-wrap break-all rounded bg-white/70 p-2 text-[10px] dark:bg-slate-900/70">
                            {JSON.stringify(Object.fromEntries(Object.entries(action.payload).filter(([key]) => key !== "_plan")), null, 2)}
                          </pre>
                        </details>
                      )}
                      {action.status === "applied" && (
                        <p className="mt-1 text-[11px] font-semibold text-teal-700 dark:text-teal-300">Cambio aplicado al diagrama.</p>
                      )}
                      {action.status === "failed" && action.error_message && (
                        <p className="mt-1 text-[11px] text-red-700" role="alert">{action.error_message}</p>
                      )}

                      {action.status === "proposed" && (
                        <div className="mt-2.5">
                          {!dependenciasAccionListas(action, store.actions) && (
                            <p className="mb-2 text-[11px] text-amber-800">Confirma primero el cambio anterior de esta propuesta.</p>
                          )}
                          {canConfirmActions ? (
                            <div className="flex gap-2">
                              <button
                                disabled={busyActionId === action.id || !dependenciasAccionListas(action, store.actions)}
                                className="inline-flex h-7 items-center gap-1 rounded-md bg-teal-700 px-2.5 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-60"
                                onClick={() => void decidirAccion(action, "confirm")}
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
                                onClick={() => void decidirAccion(action, "reject")}
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

            <div ref={endRef} />

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
                      disabled={loading || !canChat || !conversationId}
                      className="h-7 rounded-md bg-teal-700 px-2.5 text-xs font-bold text-white shadow-sm hover:bg-teal-800 disabled:opacity-60"
                      onClick={() => void prepararRecomendacion(item)}
                    >
                      {loading ? "Procesando..." : preparacionRecomendacion(item.title).kind === "automatic"
                        ? "Preparar corrección" : "Definir criterio"}
                    </button>
                    <button
                      className="h-7 rounded-md border border-current px-2.5 text-xs font-bold"
                      onClick={() => void decidirRecomendacion(item, "dismissed")}
                    >
                      Descartar
                    </button>
                  </div>
                  {recommendationGuidance?.id === item.id && (
                    <div className="mt-2 rounded-md bg-amber-50 p-2 text-[11px] leading-4 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
                      <p>{recommendationGuidance.text}</p>
                      <label htmlFor={`criterio-${item.id}`} className="mt-2 block font-semibold">
                        Tu criterio para esta mejora
                      </label>
                      <textarea
                        id={`criterio-${item.id}`}
                        value={recommendationCriterion}
                        onChange={(event) => setRecommendationCriterion(event.target.value)}
                        maxLength={1000}
                        rows={2}
                        placeholder="Indica valores, reglas o multiplicidades concretas."
                        className="mt-1 w-full rounded-md border border-amber-300 bg-white p-2 text-slate-900 dark:border-amber-700 dark:bg-slate-900 dark:text-white"
                      />
                      <button
                        type="button"
                        disabled={!recommendationCriterion.trim() || loading || !canChat || !conversationId}
                        onClick={() => void prepararConCriterio(item)}
                        className="mt-2 rounded-md bg-teal-700 px-2.5 py-1.5 font-bold text-white disabled:opacity-50"
                      >
                        {loading ? "Procesando..." : "Preparar propuesta"}
                      </button>
                      <p className="mt-1">Si puede preparar acciones concretas, podrás revisarlas antes de aplicarlas.</p>
                    </div>
                  )}
                </aside>
              ))}
          </div>

          {error && (
            <p className="border-t border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
              {error}
            </p>
          )}
          {actionFeedback && <p className="border-t border-teal-200 bg-teal-50 px-4 py-2 text-xs text-teal-800" role="status">{actionFeedback}</p>}

          {speech.error && (
            <p className="border-t border-amber-200 bg-amber-50 px-4 py-1.5 text-xs text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200">
              {speech.error}
            </p>
          )}

          {/* Compositor con soporte de voz (maqueta.html#asistente) */}
          <footer
            className={cn("shrink-0 border-t p-3", dark ? "border-slate-800" : "border-slate-200")}
          >
            {speech.escuchando && speech.transcripcionParcial && (
              <div
                className="mb-2 text-xs italic text-slate-500 bg-slate-50 dark:bg-slate-900/60 p-2 rounded-lg border border-dashed border-teal-400"
                aria-live="polite"
              >
                Dictando: {speech.transcripcionParcial}
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
                    void enviar();
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
              {speech.disponible && canChat && (
                <button
                  type="button"
                  id="mic"
                  aria-pressed={speech.escuchando}
                  aria-label="Dictar por voz"
                  title={speech.escuchando ? "Detener dictado" : "Dictar por voz"}
                  onClick={() => {
                    if (speech.escuchando) {
                      speech.detener();
                    } else {
                      speech.iniciar();
                    }
                  }}
                  className={cn(
                    "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition shadow-sm",
                    speech.escuchando
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
                id="enviar"
                aria-label="Enviar"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-teal-600 text-white shadow-sm transition hover:bg-teal-700 disabled:opacity-40"
                disabled={!draft.trim() || loading || !conversationId || !canChat}
                onClick={() => void enviar()}
                title="Enviar mensaje"
              >
                <Send size={18} />
              </button>
            </div>

            {/* Opciones del compositor */}
            {speech.disponible && canChat && (
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500">
                <label className="inline-flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    id="auto-enviar"
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
