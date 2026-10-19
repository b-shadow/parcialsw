import { describe, expect, it } from "vitest";

import { parseProjectSocketEvent } from "./projectSocket";

describe("project socket phase 1 contracts", () => {
  it("parses protocol v2 events", () => {
    const parsed = parseProjectSocketEvent(JSON.stringify({
      protocol_version: 2,
      type: "FLUTTER_THEME_UPDATED",
      event_id: "event-1",
      project_id: "project-1",
      sequence_number: 8,
      correlation_id: "correlation-1",
      occurred_at: "2026-10-15T12:00:00Z",
      actor: { display_name: "Editor" },
      payload: {}
    }));
    expect(parsed?.type).toBe("FLUTTER_THEME_UPDATED");
  });

  it("keeps v1 compatibility", () => {
    expect(parseProjectSocketEvent('{"type":"PONG"}')?.type).toBe("PONG");
  });

  it("ignores malformed payloads and wraps unknown events", () => {
    expect(parseProjectSocketEvent("not-json")).toBeNull();
    expect(parseProjectSocketEvent('{"type":"FUTURE_EVENT"}')?.type).toBe("UNKNOWN");
  });
});
