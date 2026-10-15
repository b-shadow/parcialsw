import { env } from "../config/env";
import { useAuthStore } from "../auth/authStore";

export function createProjectSocket(projectId: string): WebSocket {
  const token = useAuthStore.getState().token ?? window.localStorage.getItem("case_access_token") ?? "";
  return new WebSocket(`${env.wsBaseUrl}/ws/projects/${projectId}`, [
    "case-v1",
    `case-auth.${token}`
  ]);
}

export type ProjectSocketEvent = {
  type: "SESSION_CONNECTED" | "UML_EVENT" | "EVENT_ACK" | "EVENT_REJECTED" | "PONG";
  project_id?: string;
  diagram_id?: string | null;
  event_id?: string;
  client_event_id?: string;
  sequence_number?: number;
  duplicate?: boolean;
  event_type?: string;
  user_id?: string;
  user_name?: string;
  created_at?: string;
  reason?: string;
  server_time?: string;
  payload?: Record<string, unknown>;
};

export function sendProjectEvent(socket: WebSocket | null, payload: Record<string, unknown>) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "UML_EVENT", payload }));
  }
}
