import { beforeEach, describe, expect, it, vi } from "vitest";

import { clienteApi } from "../../../core/api/cliente";
import { servicioGeneracion } from "./servicioGeneracion";

vi.mock("../../../core/api/cliente", () => ({
  clienteApi: { get: vi.fn(), post: vi.fn() }
}));

const theme = {
  primary_color: "#0F766E",
  secondary_color: "#14B8A6",
  background_color: "#F8FAFC",
  surface_color: "#FFFFFF",
  button_color: "#0F766E",
  font_family: "Roboto",
  border_radius: 12,
  button_style: "filled" as const,
  density: "normal" as const
};

describe("phase5 coordinated generation service", () => {
  beforeEach(() => vi.clearAllMocks());

  it("runs preflight before generation", async () => {
    vi.mocked(clienteApi.post).mockResolvedValue({ data: { ready: true } });
    const payload = { transformation_id: "t-1", name: "Academico", theme_config: theme };
    await servicioGeneracion.preflightCoordinated(payload);
    expect(clienteApi.post).toHaveBeenCalledWith("/generation/coordinated/preflight", payload);
  });

  it("sends verification and idempotency choices explicitly", async () => {
    vi.mocked(clienteApi.post).mockResolvedValue({ data: { id: "g-1" } });
    const payload = {
      transformation_id: "t-1",
      name: "Academico",
      client_request_id: "request-123",
      api_base_url: "http://localhost:8080",
      verify: true,
      allow_unverified: false,
      theme_config: theme
    };
    await servicioGeneracion.coordinated(payload);
    expect(clienteApi.post).toHaveBeenCalledWith("/generation/coordinated", payload);
  });

  it("downloads the coordinated bundle", async () => {
    vi.mocked(clienteApi.get).mockResolvedValue({ data: new Blob() });
    await servicioGeneracion.downloadCoordinated("g-1");
    expect(clienteApi.get).toHaveBeenCalledWith("/generation/coordinated/g-1/download", {
      responseType: "blob"
    });
  });
});
