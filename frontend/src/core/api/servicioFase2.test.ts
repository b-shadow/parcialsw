import { beforeEach, describe, expect, it, vi } from "vitest";

import { clienteApi } from "./cliente";
import { servicioFase1 } from "./servicioFase1";

vi.mock("./cliente", () => ({
  clienteApi: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn() }
}));

describe("phase2 AI service", () => {
  beforeEach(() => vi.clearAllMocks());

  it("sends an idempotent interaction contract", async () => {
    vi.mocked(clienteApi.post).mockResolvedValue({ data: { answer: "ok" } });
    const payload = { client_message_id: crypto.randomUUID(), content: "Revisa y mejora" };
    await servicioFase1.interactuar("project-1", payload);
    expect(clienteApi.post).toHaveBeenCalledWith("/projects/project-1/ai/interactions", payload);
  });

  it("uses explicit confirm and reject endpoints", async () => {
    vi.mocked(clienteApi.post).mockResolvedValue({ data: {} });
    await servicioFase1.confirmarAccionIA("p", "a");
    await servicioFase1.rechazarAccionIA("p", "a");
    expect(clienteApi.post).toHaveBeenNthCalledWith(1, "/projects/p/ai/actions/a/confirm");
    expect(clienteApi.post).toHaveBeenNthCalledWith(2, "/projects/p/ai/actions/a/reject");
  });

  it("reads provider health", async () => {
    vi.mocked(clienteApi.get).mockResolvedValue({ data: { available: false } });
    await servicioFase1.estadoProveedorIA("project-1");
    expect(clienteApi.get).toHaveBeenCalledWith("/projects/project-1/ai/provider-health");
  });

  it("contains malformed assistant collections instead of crashing the workspace", async () => {
    vi.mocked(clienteApi.get).mockResolvedValue({ data: { items: [] } });

    await expect(servicioFase1.listarAcciones("project-1")).resolves.toEqual([]);
    await expect(servicioFase1.listarRecomendaciones("project-1")).resolves.toEqual([]);
  });
});
