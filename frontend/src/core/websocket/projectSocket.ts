import { useAuthStore } from "../auth/authStore";
import { env } from "../config/env";
import type { ProjectSocketEventV2 } from "../contracts/phase1";

const V1_EVENTS = new Set(["SESSION_CONNECTED", "UML_EVENT", "EVENT_ACK", "EVENT_REJECTED", "PONG"]);
const V2_EVENTS = new Set([
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

export type ProjectSocketEvent = {
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

export type ParsedProjectSocketEvent = ProjectSocketEvent | ProjectSocketEventV2 | {
  type: "UNKNOWN";
  raw: Record<string, unknown>;
};

export type ProjectSocketStatus = "connecting" | "connected" | "reconnecting" | "disconnected";

function authProtocols() {
  const token = useAuthStore.getState().token ?? window.localStorage.getItem("case_access_token") ?? "";
  return ["case-v1", `case-auth.${token}`];
}

export function createProjectSocket(projectId: string): WebSocket {
  return new WebSocket(`${env.wsBaseUrl}/ws/projects/${projectId}`, authProtocols());
}

export function parseProjectSocketEvent(raw: string): ParsedProjectSocketEvent | null {
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    const record = value as Record<string, unknown>;
    if (record.protocol_version === 2 && typeof record.type === "string") {
      return V2_EVENTS.has(record.type)
        ? record as ProjectSocketEventV2
        : { type: "UNKNOWN", raw: record };
    }
    if (typeof record.type === "string") {
      return V1_EVENTS.has(record.type)
        ? record as ProjectSocketEvent
        : { type: "UNKNOWN", raw: record };
    }
    return null;
  } catch {
    return null;
  }
}

export function sendProjectEvent(socket: WebSocket | null, payload: Record<string, unknown>) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "UML_EVENT", payload }));
  }
}

type SocketClientOptions = {
  projectId: string;
  getProjectSequence: () => number;
  getConversationSequence: () => number;
  onEvent: (event: ParsedProjectSocketEvent) => void;
  onStatus: (status: ProjectSocketStatus) => void;
};

export class ProjectSocketClient {
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
    const socket = createProjectSocket(this.options.projectId);
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
      const parsed = parseProjectSocketEvent(String(message.data));
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
      this.socket.send(JSON.stringify(payload));
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
    this.socket?.close(1000, "client_close");
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
