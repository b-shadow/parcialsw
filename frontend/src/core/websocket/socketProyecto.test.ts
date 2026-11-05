import { afterEach, describe, expect, it, vi } from "vitest";

import { useAlmacenAutenticacion } from "../auth/almacenAutenticacion";
import { crearSocketProyecto, analizarEventoSocketProyecto, ClienteSocketProyecto, enviarEventoProyecto } from "./socketProyecto";

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
  it("reconoce la actualización UML publicada tras confirmar una acción de IA", () => {
    const event = analizarEventoSocketProyecto(JSON.stringify({
      protocol_version: 2,
      type: "UML_EVENT",
      diagram_id: "diagram-1",
      payload: { event_type: "AI_UPDATE_DIAGRAM" },
    }));
    expect(event?.type).toBe("UML_EVENT");
  });
  afterEach(() => {
    useAlmacenAutenticacion.getState().setToken(null);
    vi.unstubAllGlobals();
  });

  it("autentica la conexion y serializa eventos UML", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    useAlmacenAutenticacion.getState().setToken("token.seguro_123");

    const socket = crearSocketProyecto("project-1") as unknown as MockWebSocket;
    enviarEventoProyecto(socket as unknown as WebSocket, {
      action: "UPDATE_CLASS",
      diagram_id: "diagram-1"
    });

    expect(socket.url).toContain("/ws/projects/project-1");
    expect(socket.url).toContain("contrato=es");
    expect(socket.url).not.toContain("token");
    expect(socket.protocols).toEqual(["case-v1", "case-auth.token.seguro_123"]);
    expect(socket.sent).toEqual([
      JSON.stringify({
        tipo: "UML_EVENT",
        carga_datos: { accion: "UPDATE_CLASS", diagrama_id: "diagram-1" }
      })
    ]);
  });

  it("envia ambos cursores al abrir para detectar brechas", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    const statuses: string[] = [];
    const client = new ClienteSocketProyecto({
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
      tipo: "SYNC_STATE",
      ultima_secuencia_proyecto: 21,
      ultima_secuencia_conversacion: 9
    });
    expect(statuses).toEqual(["connecting", "connected"]);
    client.close();
  });

  it("espera la apertura antes de cerrar una conexion en progreso", () => {
    vi.stubGlobal("WebSocket", MockWebSocket);
    const client = new ClienteSocketProyecto({
      projectId: "project-1",
      getProjectSequence: () => 0,
      getConversationSequence: () => 0,
      onEvent: () => undefined,
      onStatus: () => undefined
    });
    client.connect();
    const socket = (client as unknown as { socket: MockWebSocket }).socket;
    socket.readyState = MockWebSocket.CONNECTING;

    client.close();
    expect(socket.readyState).toBe(MockWebSocket.CONNECTING);
    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    expect(socket.readyState).toBe(3);
    expect(socket.sent).toEqual([]);
  });
});
