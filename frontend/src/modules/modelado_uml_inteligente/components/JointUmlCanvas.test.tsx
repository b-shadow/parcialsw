import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ElementLock } from "../../../core/contracts/mejoras2p";
import { JointUmlCanvas } from "./JointUmlCanvas";
import type { UmlClassDetail, UmlRelationship } from "../types/uml";

const emptyClass: UmlClassDetail = {
  id: "class-1",
  diagram_id: "diagram-1",
  name: "Cliente",
  visibility: "public",
  element_type: "class",
  stereotype: null,
  description: null,
  metadata_json: {},
  attributes: [],
  methods: [],
  visual: null
};

function renderCanvas(
  umlClass: UmlClassDetail,
  relationships: UmlRelationship[] = [],
  extraClasses: UmlClassDetail[] = [],
  lockedElements?: Record<string, ElementLock>
) {
  return render(
    <JointUmlCanvas
      activeTool="select"
      classes={[umlClass, ...extraClasses]}
      isDark={false}
      lockedElements={lockedElements}
      onClassClick={vi.fn()}
      onClassMove={vi.fn()}
      onClassRename={vi.fn()}
      onRelationshipClick={vi.fn()}
      pendingSourceId=""
      relationships={relationships}
      selectedClassId={null}
      selectedRelationshipId={null}
    />
  );
}

describe("JointUmlCanvas class members", () => {
  it("leaves empty compartments blank instead of rendering phantom members", () => {
    renderCanvas(emptyClass);

    expect(screen.queryByText(/validar\(\)/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/id:\s*Long/i)).not.toBeInTheDocument();
  });

  it("renders a method only after it exists in the class model", () => {
    renderCanvas({
      ...emptyClass,
      methods: [
        {
          id: "method-1",
          class_id: emptyClass.id,
          name: "guardar",
          return_type: "void",
          visibility: "public",
          order_index: 0,
          metadata_json: {},
          parameters: []
        }
      ]
    });

    expect(screen.getByText(/guardar\(\): void/i)).toBeInTheDocument();
  });

  it.each([
    ["inheritance", "uml-generalization"],
    ["aggregation", "uml-aggregation"],
    ["composition", "uml-composition"]
  ])("renders the UML marker for %s", (relationshipType, markerId) => {
    const targetClass: UmlClassDetail = {
      ...emptyClass,
      id: "class-2",
      name: "Destino",
      visual: {
        id: "visual-2",
        diagram_id: "diagram-1",
        element_type: "class",
        element_id: "class-2",
        position_x: 500,
        position_y: 100,
        width: null,
        height: null,
        style: {}
      }
    };
    const relationship: UmlRelationship = {
      id: `relationship-${relationshipType}`,
      diagram_id: "diagram-1",
      source_class_id: emptyClass.id,
      target_class_id: targetClass.id,
      relationship_type: relationshipType,
      source_cardinality: "0..*",
      target_cardinality: "1",
      direction: "source_to_target",
      label: relationshipType,
      metadata_json: {}
    };

    const { container } = renderCanvas(emptyClass, [relationship], [targetClass]);

    expect(container.querySelector(`[id="${markerId}"]`)).toBeInTheDocument();
    expect(
      [...container.querySelectorAll("line")].some((line) => line.getAttribute("marker-end") === `url(#${markerId})`)
    ).toBe(true);
  });

  it("interfaz muestra «interface» sobre el nombre", () => {
    renderCanvas({
      ...emptyClass,
      element_type: "interface",
      name: "Repositorio"
    });

    expect(screen.getByText("«interface»")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Repositorio")).toBeInTheDocument();
  });

  it("clase abstracta muestra el nombre en cursiva", () => {
    renderCanvas({
      ...emptyClass,
      element_type: "abstract_class",
      name: "EntidadBase"
    });

    const input = screen.getByDisplayValue("EntidadBase");
    expect(input.className).toContain("italic");
  });

  it("visibilidades se dibujan como + - # ~", () => {
    renderCanvas({
      ...emptyClass,
      attributes: [
        {
          id: "attr-pub",
          class_id: emptyClass.id,
          name: "campoPublico",
          data_type: "String",
          visibility: "public",
          initial_value: null,
          multiplicity: null,
          is_required: true,
          order_index: 0,
          constraints: {}
        },
        {
          id: "attr-priv",
          class_id: emptyClass.id,
          name: "campoPrivado",
          data_type: "Integer",
          visibility: "private",
          initial_value: null,
          multiplicity: null,
          is_required: true,
          order_index: 1,
          constraints: {}
        },
        {
          id: "attr-prot",
          class_id: emptyClass.id,
          name: "campoProtegido",
          data_type: "Boolean",
          visibility: "protected",
          initial_value: null,
          multiplicity: null,
          is_required: false,
          order_index: 2,
          constraints: {}
        },
        {
          id: "attr-pack",
          class_id: emptyClass.id,
          name: "campoPaquete",
          data_type: "Double",
          visibility: "package",
          initial_value: null,
          multiplicity: null,
          is_required: false,
          order_index: 3,
          constraints: {}
        }
      ]
    });

    expect(screen.getByText(/\+\s+campoPublico:\s*String/)).toBeInTheDocument();
    expect(screen.getByText(/-\s+campoPrivado:\s*Integer/)).toBeInTheDocument();
    expect(screen.getByText(/#\s+campoProtegido:\s*Boolean/)).toBeInTheDocument();
    expect(screen.getByText(/~\s+campoPaquete:\s*Double/)).toBeInTheDocument();
  });

  it("realización usa línea punteada con marcador de triángulo hueco", () => {
    const targetClass: UmlClassDetail = {
      ...emptyClass,
      id: "class-interface",
      name: "ServicioRemoto",
      element_type: "interface"
    };
    const relationship: UmlRelationship = {
      id: "rel-realization",
      diagram_id: "diagram-1",
      source_class_id: emptyClass.id,
      target_class_id: targetClass.id,
      relationship_type: "realization",
      source_cardinality: "1",
      target_cardinality: "1",
      direction: "source_to_target",
      label: "realiza",
      metadata_json: {}
    };

    const { container } = renderCanvas(emptyClass, [relationship], [targetClass]);

    expect(container.querySelector('[id="uml-realization"]')).toBeInTheDocument();
    const line = [...container.querySelectorAll("line")].find(
      (l) => l.getAttribute("marker-end") === "url(#uml-realization)"
    );
    expect(line).toBeDefined();
    expect(line?.getAttribute("stroke-dasharray")).toBe("8 6");
  });

  it("lockedElements con la clase -> muestra candado con el nombre", () => {
    const lockedElements: Record<string, ElementLock> = {
      [emptyClass.id]: {
        diagram_id: "diagram-1",
        element_type: "class",
        element_id: emptyClass.id,
        locked_by: {
          user_id: "user-42",
          display_name: "Lucia Dev"
        },
        expires_at: new Date(Date.now() + 60000).toISOString()
      }
    };

    renderCanvas(emptyClass, [], [], lockedElements);

    expect(screen.getByText(/Lucia Dev editando/i)).toBeInTheDocument();
    expect(screen.getByText("🔒")).toBeInTheDocument();
  });
});
