import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../../../core/api/client";
import { generationService } from "./generationService";

vi.mock("../../../core/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn() }
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
    vi.mocked(apiClient.post).mockResolvedValue({ data: { ready: true } });
    const payload = { transformation_id: "t-1", name: "Academico", theme_config: theme };
    await generationService.preflightCoordinated(payload);
    expect(apiClient.post).toHaveBeenCalledWith("/generation/coordinated/preflight", payload);
  });

  it("sends verification and idempotency choices explicitly", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: { id: "g-1" } });
    const payload = {
      transformation_id: "t-1",
      name: "Academico",
      client_request_id: "request-123",
      api_base_url: "http://localhost:8080",
      verify: true,
      allow_unverified: false,
      theme_config: theme
    };
    await generationService.coordinated(payload);
    expect(apiClient.post).toHaveBeenCalledWith("/generation/coordinated", payload);
  });

  it("downloads the coordinated bundle", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: new Blob() });
    await generationService.downloadCoordinated("g-1");
    expect(apiClient.get).toHaveBeenCalledWith("/generation/coordinated/g-1/download", {
      responseType: "blob"
    });
  });
});
