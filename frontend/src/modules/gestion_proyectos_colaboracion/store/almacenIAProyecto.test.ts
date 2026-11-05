import { beforeEach, describe, expect, it } from "vitest";

import type { MensajeIA, PresenciaProyecto } from "../../../core/contracts/phase1";
import { ultimaSecuenciaContinuaMensajes, useAlmacenIAProyecto } from "./almacenIAProyecto";

function message(sequence: number, content = `Mensaje ${sequence}`): MensajeIA {
  return {
    id: `message-${sequence}`,
    conversation_id: "conversation",
    project_id: "project-a",
    author_user_id: "user-a",
    author_display_name: "Ana",
    role: "user",
    content,
    sequence_number: sequence,
    client_message_id: `client-${sequence}`,
    correlation_id: `correlation-${sequence}`,
    status: "completed",
    detected_intents: [],
    references_json: [],
    metadata_json: {},
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z"
  };
}

function presence(userId: string, displayName: string, connections = 1): PresenciaProyecto {
  return {
    user_id: userId,
    display_name: displayName,
    project_role: "EDITOR",
    connection_count: connections,
    active_diagram_id: null
  };
}

describe("projectAiStore", () => {
  beforeEach(() => useAlmacenIAProyecto.getState().initialize(`project-${crypto.randomUUID()}`));

  it("ordena y deduplica mensajes recibidos por REST y WebSocket", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setHistory([message(2), message(1)], false);
    store.upsertMessage(message(2, "Actualizado"));

    expect(useAlmacenIAProyecto.getState().messages.map((item) => item.sequence_number)).toEqual([1, 2]);
    expect(useAlmacenIAProyecto.getState().messages[1].content).toBe("Actualizado");
    expect(useAlmacenIAProyecto.getState().conversationSequence).toBe(2);
  });

  it("conserva mensajes WebSocket que llegan antes del historial REST", () => {
    const store = useAlmacenIAProyecto.getState();
    store.upsertMessage(message(3));
    store.setHistory([message(1), message(2)], false);

    expect(useAlmacenIAProyecto.getState().messages.map((item) => item.sequence_number)).toEqual([1, 2, 3]);
    expect(useAlmacenIAProyecto.getState().conversationSequence).toBe(3);
  });

  it("sincroniza desde el ultimo mensaje continuo si falta uno intermedio", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setHistory([message(1), message(3)], false);

    expect(ultimaSecuenciaContinuaMensajes(useAlmacenIAProyecto.getState().messages)).toBe(1);
    store.upsertMessage(message(2));
    expect(ultimaSecuenciaContinuaMensajes(useAlmacenIAProyecto.getState().messages)).toBe(3);
  });

  it("no retrocede cursores frente a eventos fuera de orden", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setSequences(20, 10);
    store.setSequences(18, 8);

    expect(useAlmacenIAProyecto.getState().projectSequence).toBe(20);
    expect(useAlmacenIAProyecto.getState().conversationSequence).toBe(10);
  });

  it("reinicia datos al cambiar de proyecto", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setHistory([message(1)], true);
    store.initialize("another-project");

    expect(useAlmacenIAProyecto.getState().messages).toEqual([]);
    expect(useAlmacenIAProyecto.getState().projectId).toBe("another-project");
  });

  it("mantiene la presencia ordenada y sin duplicar usuarios reconectados", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setPresence([presence("user-b", "Bruno"), presence("user-a", "Ana")]);
    store.upsertPresence(presence("user-a", "Ana Maria", 2));

    expect(useAlmacenIAProyecto.getState().presence).toEqual([
      presence("user-a", "Ana Maria", 2),
      presence("user-b", "Bruno")
    ]);
  });

  it("retira de inmediato al integrante que abandona el proyecto", () => {
    const store = useAlmacenIAProyecto.getState();
    store.setPresence([presence("user-a", "Ana"), presence("user-b", "Bruno")]);
    store.removePresence("user-a");

    expect(useAlmacenIAProyecto.getState().presence).toEqual([presence("user-b", "Bruno")]);
  });
});
