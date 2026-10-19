import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../auth/authStore";
import { createProjectSocket, ProjectSocketClient, sendProjectEvent } from "./projectSocket";

class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  readonly url: string;
  readonly protocols: string[];
  readyState = MockWebSocket.OPEN;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((message: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(url: string, protocols: string[] = []) {
    this.url = url;
    this.protocols = protocols;
  }

  send(value: string) {
    this.sent.push(value);
  }

  close() {
    this.readyState = 3;
    this.onclose?.();
  }
}

describe("projectSocket", () => {
  afterEach(() => {
    useAuthStore.getState().setToken(null);
    vi.unstubAllGlobals();
  });

  it("autentica la conexion y serializa eventos UML", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    useAuthStore.getState().setToken("token.seguro_123");

    const socket = createProjectSocket("project-1") as unknown as MockWebSocket;
    sendProjectEvent(socket as unknown as WebSocket, {
      action: "UPDATE_CLASS",
      diagram_id: "diagram-1"
    });

    expect(socket.url).toContain("/ws/projects/project-1");
    expect(socket.url).not.toContain("token");
    expect(socket.protocols).toEqual(["case-v1", "case-auth.token.seguro_123"]);
    expect(socket.sent).toEqual([
      JSON.stringify({
        type: "UML_EVENT",
        payload: { action: "UPDATE_CLASS", diagram_id: "diagram-1" }
      })
    ]);
  });

  it("envia ambos cursores al abrir para detectar brechas", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    const statuses: string[] = [];
    const client = new ProjectSocketClient({
      projectId: "project-1",
      getProjectSequence: () => 21,
      getConversationSequence: () => 9,
      onEvent: () => undefined,
      onStatus: (status) => statuses.push(status)
    });

    client.connect();
    const socket = (client as unknown as { socket: MockWebSocket }).socket;
    socket.onopen?.();

    expect(JSON.parse(socket.sent[0])).toEqual({
      type: "SYNC_STATE",
      last_project_sequence: 21,
      last_conversation_sequence: 9
    });
    expect(statuses).toEqual(["connecting", "connected"]);
    client.close();
  });
});
