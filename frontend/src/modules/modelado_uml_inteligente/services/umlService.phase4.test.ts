import { beforeEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../../../core/api/client";
import { umlService } from "./umlService";

vi.mock("../../../core/api/client", () => ({
  apiClient: {
    get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn()
  }
}));

const draft = {
  description: "Registrar una inscripcion",
  operation_kind: "create" as const,
  exposure: "internal" as const,
  preconditions: [],
  postconditions: [],
  business_rules: [],
  validations: [],
  side_effects: [],
  required_permissions: [],
  related_entities: [],
  backend_contract: null,
  frontend_contract: null,
  schema_version: 1 as const
};

describe("phase 4 UML method contracts", () => {
  beforeEach(() => vi.clearAllMocks());

  it("creates once with If-None-Match", async () => {
    vi.mocked(apiClient.put).mockResolvedValue({ data: { revision: 1 } });

    await umlService.saveMethodSpecification("method-1", draft, null);

    expect(apiClient.put).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      draft,
      { headers: { "If-None-Match": "*" } }
    );
  });

  it("updates and deletes with the current revision", async () => {
    vi.mocked(apiClient.put).mockResolvedValue({ data: { revision: 5 } });
    vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined });

    await umlService.saveMethodSpecification("method-1", draft, 4);
    await umlService.deleteMethodSpecification("method-1", 5);

    expect(apiClient.put).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      draft,
      { headers: { "If-Match": '"revision-4"' } }
    );
    expect(apiClient.delete).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      { headers: { "If-Match": '"revision-5"' } }
    );
  });

  it("uses strict validation and an idempotent refinement message", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ data: {} });

    await umlService.validateMethodSpecification("method-1", true);
    await umlService.refineMethodSpecification("method-1", "Crear formulario", 3);

    expect(apiClient.post).toHaveBeenNthCalledWith(
      1,
      "/uml/methods/method-1/specification/validate",
      undefined,
      { params: { strict: true } }
    );
    const refinement = vi.mocked(apiClient.post).mock.calls[1][1] as Record<string, unknown>;
    expect(refinement).toMatchObject({ instruction: "Crear formulario", base_revision: 3 });
    expect(refinement.client_message_id).toEqual(expect.any(String));
  });
});
