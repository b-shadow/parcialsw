import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { phase1Service } from "../../../core/api/phase1Service";
import { umlService } from "../services/umlService";
import type { UmlClassDetail, UmlMethod } from "../types/uml";
import { MethodSpecificationEditor } from "./MethodSpecificationEditor";

vi.mock("../../../core/api/phase1Service", () => ({
  phase1Service: { confirmAiAction: vi.fn(), rejectAiAction: vi.fn() }
}));

vi.mock("../../../core/websocket/projectSocket", () => ({
  ProjectSocketClient: class {
    connect() {}
    setActiveDiagram() {}
    close() {}
  }
}));

vi.mock("../services/umlService", () => ({
  umlService: {
    methodSpecification: vi.fn(),
    saveMethodSpecification: vi.fn(),
    validateMethodSpecification: vi.fn(),
    refineMethodSpecification: vi.fn(),
    updateMethod: vi.fn(),
    addParameter: vi.fn(),
    updateParameter: vi.fn(),
    deleteParameter: vi.fn()
  }
}));

const method: UmlMethod = {
  id: "method-1",
  class_id: "class-1",
  name: "registrar",
  return_type: "void",
  visibility: "public",
  order_index: 0,
  metadata_json: {},
  parameters: []
};

const umlClass: UmlClassDetail = {
  id: "class-1",
  diagram_id: "diagram-1",
  name: "Inscripcion",
  visibility: "public",
  element_type: "class",
  stereotype: null,
  description: null,
  metadata_json: {},
  attributes: [],
  methods: [method],
  visual: null
};

const readiness = {
  status: "empty" as const,
  ready_for_generation: false,
  errors: [],
  warnings: [],
  inferred_fields: []
};

function mount() {
  return render(
    <MethodSpecificationEditor
      projectId="project-1"
      diagramId="diagram-1"
      umlClass={umlClass}
      classes={[umlClass]}
      method={method}
      dark={false}
      onClose={vi.fn()}
      onMethodChange={vi.fn()}
    />
  );
}

describe("MethodSpecificationEditor phase 4", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(umlService.methodSpecification).mockResolvedValue({
      specification: null,
      readiness
    });
    vi.mocked(phase1Service.rejectAiAction).mockResolvedValue({} as never);
  });

  it("exposes the five editing views on the selected method", async () => {
    mount();
    await waitFor(() => expect(umlService.methodSpecification).toHaveBeenCalledWith("method-1"));

    for (const label of ["Firma", "Comportamiento", "Backend", "Flutter", "Validacion"]) {
      expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    }
    fireEvent.click(screen.getByRole("button", { name: "Comportamiento" }));
    expect(screen.getByText("Efectos laterales")).toBeInTheDocument();
    expect(screen.getByText("Entidades relacionadas")).toBeInTheDocument();
  });

  it("records rejection instead of only hiding the AI proposal", async () => {
    vi.mocked(umlService.refineMethodSpecification).mockResolvedValue({
      action_id: "action-1",
      method_id: "method-1",
      base_revision: 0,
      summary: "Propuesta funcional",
      patch: { description: "Registrar con validacion" },
      changed_fields: ["description"],
      unresolved_references: [],
      assumptions: [],
      warnings: [],
      validation: readiness,
      provider: "rule_engine",
      fallback_used: false
    });
    mount();
    fireEvent.change(screen.getByPlaceholderText(/Describe que debe hacer/), {
      target: { value: "Completa el metodo" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Proponer" }));
    await screen.findByText("Propuesta funcional");
    fireEvent.click(screen.getByRole("button", { name: "Rechazar" }));

    await waitFor(() =>
      expect(phase1Service.rejectAiAction).toHaveBeenCalledWith("project-1", "action-1")
    );
  });

  it("incorporates selected proposal fields into the local draft", async () => {
    vi.mocked(umlService.refineMethodSpecification).mockResolvedValue({
      action_id: "action-2",
      method_id: "method-1",
      base_revision: 0,
      summary: "Seleccion parcial",
      patch: { description: "Descripcion propuesta", operation_kind: "create" },
      changed_fields: ["description", "operation_kind"],
      unresolved_references: [],
      assumptions: [],
      warnings: [],
      validation: readiness,
      provider: "rule_engine",
      fallback_used: false
    });
    mount();
    fireEvent.change(screen.getByPlaceholderText(/Describe que debe hacer/), {
      target: { value: "Completa dos campos" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Proponer" }));
    await screen.findByText("Seleccion parcial");
    fireEvent.click(screen.getByRole("button", { name: "Incorporar seleccion al borrador" }));

    await waitFor(() => expect(phase1Service.rejectAiAction).toHaveBeenCalled());
    expect(screen.getByRole("button", { name: "Guardar borrador" })).toBeEnabled();
  });
});
