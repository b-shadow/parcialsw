import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "./client";
import { phase1Service } from "./phase1Service";

vi.mock("./client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn() }
}));

describe("phase2 AI service", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sends an idempotent interaction contract", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { answer: "ok" } });
    const payload = { client_message_id: crypto.randomUUID(), content: "Revisa y mejora" };
    await phase1Service.interact("project-1", payload);
    expect(apiClient.post).toHaveBeenCalledWith("/projects/project-1/ai/interactions", payload);
  });

  it("uses explicit confirm and reject endpoints", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: {} });
    await phase1Service.confirmAiAction("p", "a");
    await phase1Service.rejectAiAction("p", "a");
    expect(apiClient.post).toHaveBeenNthCalledWith(1, "/projects/p/ai/actions/a/confirm");
    expect(apiClient.post).toHaveBeenNthCalledWith(2, "/projects/p/ai/actions/a/reject");
  });

  it("reads provider health", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { available: false } });
    await phase1Service.aiProviderHealth("project-1");
    expect(apiClient.get).toHaveBeenCalledWith("/projects/project-1/ai/provider-health");
  });

  it("contains malformed assistant collections instead of crashing the workspace", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { items: [] } });

    await expect(phase1Service.actions("project-1")).resolves.toEqual([]);
    await expect(phase1Service.recommendations("project-1")).resolves.toEqual([]);
  });
});
