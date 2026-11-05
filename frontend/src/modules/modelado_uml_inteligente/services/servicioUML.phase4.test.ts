import { beforeEach, describe, expect, it, vi } from "vitest";

import { clienteApi } from "../../../core/api/cliente";
import { servicioUML } from "./servicioUML";

vi.mock("../../../core/api/cliente", () => ({
  clienteApi: {
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
    vi.mocked(clienteApi.put).mockResolvedValue({ data: { revision: 1 } });

    await servicioUML.saveMethodSpecification("method-1", draft, null);

    expect(clienteApi.put).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      draft,
      { headers: { "If-None-Match": "*" } }
    );
  });

  it("updates and deletes with the current revision", async () => {
    vi.mocked(clienteApi.put).mockResolvedValue({ data: { revision: 5 } });
    vi.mocked(clienteApi.delete).mockResolvedValue({ data: undefined });

    await servicioUML.saveMethodSpecification("method-1", draft, 4);
    await servicioUML.deleteMethodSpecification("method-1", 5);

    expect(clienteApi.put).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      draft,
      { headers: { "If-Match": '"revision-4"' } }
    );
    expect(clienteApi.delete).toHaveBeenCalledWith(
      "/uml/methods/method-1/specification",
      { headers: { "If-Match": '"revision-5"' } }
    );
  });

  it("uses strict validation and an idempotent refinement message", async () => {
    vi.mocked(clienteApi.post).mockResolvedValue({ data: {} });

    await servicioUML.validateMethodSpecification("method-1", true);
    await servicioUML.refineMethodSpecification("method-1", "Crear formulario", 3);

    expect(clienteApi.post).toHaveBeenNthCalledWith(
      1,
      "/uml/methods/method-1/specification/validate",
      undefined,
      { params: { strict: true } }
    );
    const refinement = vi.mocked(clienteApi.post).mock.calls[1][1] as Record<string, unknown>;
    expect(refinement).toMatchObject({ instruction: "Crear formulario", base_revision: 3 });
    expect(refinement.client_message_id).toEqual(expect.any(String));
  });
});
