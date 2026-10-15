import { afterEach, describe, expect, it, vi } from "vitest";

import { useAuthStore } from "../auth/authStore";
import { createProjectSocket, sendProjectEvent } from "./projectSocket";

class MockWebSocket {
  static readonly OPEN = 1;
  readonly url: string;
  readonly protocols: string[];
  readyState = MockWebSocket.OPEN;
  sent: string[] = [];

  constructor(url: string, protocols: string[] = []) {
    this.url = url;
    this.protocols = protocols;
  }

  send(value: string) {
    this.sent.push(value);
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
});
