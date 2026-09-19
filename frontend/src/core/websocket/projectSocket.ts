import { env } from "../config/env";

export function createProjectSocket(projectId: string): WebSocket {
  return new WebSocket(`${env.wsBaseUrl}/ws/projects/${projectId}`);
}

export type ProjectSocketEvent = {
  type: "UML_EVENT" | "EVENT_ACK" | "USER_JOINED" | "USER_LEFT";
  project_id?: string;
  payload?: Record<string, unknown>;
};

export function sendProjectEvent(socket: WebSocket | null, payload: Record<string, unknown>) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "UML_EVENT", payload }));
  }
}
