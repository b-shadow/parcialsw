import { useAlmacenAutenticacion } from "../auth/almacenAutenticacion";
import { entorno } from "../config/entorno";
import type { EventoSocketProyectoV2 } from "../contracts/phase1";
import { contratoAlCodigo, contratoAlEspanol } from "../api/contratoEspanol";

const V1_EVENTS = new Set(["SESSION_CONNECTED", "UML_EVENT", "EVENT_ACK", "EVENT_REJECTED", "PONG"]);
const V2_EVENTS = new Set([
  "UML_EVENT",
  "AI_MESSAGE_CREATED", "AI_MESSAGE_STATUS_CHANGED", "AI_ACTION_PROPOSED",
  "AI_ACTION_STATUS_CHANGED", "AI_RECOMMENDATION_CREATED",
  "AI_RECOMMENDATION_STATUS_CHANGED", "AI_CONVERSATION_SUMMARY_UPDATED",
  "AI_PROCESSING_STARTED", "AI_PROCESSING_FINISHED", "AI_PROCESSING_FAILED",
  "PRESENCE_JOINED", "PRESENCE_LEFT", "PRESENCE_SNAPSHOT", "SYNC_REQUIRED",
  "FLUTTER_THEME_UPDATED", "PROJECT_VERSION_CREATED", "PROJECT_VERSION_RESTORED",
  "PROJECT_ACTIVITY_APPENDED", "PROJECT_STATE_INVALIDATED", "NOTIFICATION_CREATED", "NOTIFICATION_READ"
  , "METHOD_SIGNATURE_UPDATED", "METHOD_SPECIFICATION_CREATED",
  "METHOD_SPECIFICATION_UPDATED", "METHOD_SPECIFICATION_DELETED",
  "METHOD_SPECIFICATION_REFINED"
]);

export type EventoSocketProyecto = {
  type: "SESSION_CONNECTED" | "UML_EVENT" | "EVENT_ACK" | "EVENT_REJECTED" | "PONG";
  project_id?: string;
  diagram_id?: string | null;
  event_id?: string;
  client_event_id?: string;
  sequence_number?: number;
  conversation_sequence?: number;
  duplicate?: boolean;
  event_type?: string;
  user_id?: string;
  user_name?: string;
  created_at?: string;
  reason?: string;
  server_time?: string;
  payload?: Record<string, unknown>;
};

export type EventoSocketProyectoAnalizado = EventoSocketProyecto | EventoSocketProyectoV2 | {
  type: "UNKNOWN";
  raw: Record<string, unknown>;
};

export type EstadoSocketProyecto = "connecting" | "connected" | "reconnecting" | "disconnected";

function authProtocols() {
  const token = useAlmacenAutenticacion.getState().token ?? window.localStorage.getItem("case_access_token") ?? "";
  return ["case-v1", `case-auth.${token}`];
}

export function crearSocketProyecto(projectId: string): WebSocket {
  return new WebSocket(`${entorno.wsBaseUrl}/ws/projects/${projectId}?contrato=es`, authProtocols());
}

export function analizarEventoSocketProyecto(raw: string): EventoSocketProyectoAnalizado | null {
  try {
    const value: unknown = contratoAlCodigo(JSON.parse(raw));
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const record = value as Record<string, unknown>;
    if (record.protocol_version === 2 && typeof record.type === "string") {
      return V2_EVENTS.has(record.type)
        ? record as EventoSocketProyectoV2
        : { type: "UNKNOWN", raw: record };
    }
    if (typeof record.type === "string") {
      return V1_EVENTS.has(record.type)
        ? record as EventoSocketProyecto
        : { type: "UNKNOWN", raw: record };
    }
    return null;
  } catch {
    return null;
  }
}

export function enviarEventoProyecto(socket: WebSocket | null, payload: Record<string, unknown>) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(contratoAlEspanol({ type: "UML_EVENT", payload })));
  }
}

type SocketClientOptions = {
  projectId: string;
  getProjectSequence: () => number;
  getConversationSequence: () => number;
  onEvent: (event: EventoSocketProyectoAnalizado) => void;
  onStatus: (status: EstadoSocketProyecto) => void;
};

export class ClienteSocketProyecto {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private heartbeatTimer: number | null = null;
  private attempts = 0;
  private manuallyClosed = false;
  private readonly seenEventIds = new Set<string>();

  constructor(private readonly options: SocketClientOptions) {}

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) return;
    this.manuallyClosed = false;
    this.options.onStatus(this.attempts ? "reconnecting" : "connecting");
    const socket = crearSocketProyecto(this.options.projectId);
    this.socket = socket;
    socket.onopen = () => {
      this.attempts = 0;
      this.options.onStatus("connected");
      this.send({
        type: "SYNC_STATE",
        last_project_sequence: this.options.getProjectSequence(),
        last_conversation_sequence: this.options.getConversationSequence()
      });
      this.startHeartbeat();
    };
    socket.onmessage = (message) => {
      const parsed = analizarEventoSocketProyecto(String(message.data));
      if (!parsed) return;
      window.dispatchEvent(new CustomEvent("case:project-socket-event", { detail: parsed }));
      if ("event_id" in parsed && parsed.event_id) {
        if (this.seenEventIds.has(parsed.event_id)) return;
        this.seenEventIds.add(parsed.event_id);
        if (this.seenEventIds.size > 500) {
          const oldest = this.seenEventIds.values().next().value;
          if (oldest) this.seenEventIds.delete(oldest);
        }
      }
      this.options.onEvent(parsed);
    };
    socket.onerror = () => socket.close();
    socket.onclose = () => {
      this.stopHeartbeat();
      this.socket = null;
      if (this.manuallyClosed) {
        this.options.onStatus("disconnected");
        return;
      }
      this.scheduleReconnect();
    };
  }

  send(payload: Record<string, unknown>) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(contratoAlEspanol(payload)));
      return true;
    }
    return false;
  }

  setActiveDiagram(diagramId: string | null) {
    this.send({ type: "ACTIVE_DIAGRAM", diagram_id: diagramId });
  }

  close() {
    this.manuallyClosed = true;
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.stopHeartbeat();
    const socket = this.socket;
    if (socket?.readyState === WebSocket.CONNECTING) {
      socket.onopen = () => socket.close(1000, "client_close");
    } else {
      socket?.close(1000, "client_close");
    }
    this.socket = null;
    this.options.onStatus("disconnected");
  }

  private scheduleReconnect() {
    this.attempts += 1;
    this.options.onStatus("reconnecting");
    const base = Math.min(30_000, 1_000 * 2 ** Math.min(this.attempts - 1, 5));
    const delay = Math.round(base * (0.8 + Math.random() * 0.4));
    this.reconnectTimer = window.setTimeout(() => this.connect(), delay);
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = window.setInterval(() => this.send({ type: "PING" }), 20_000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer !== null) window.clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = null;
  }
}
