import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

function renderCanvas(umlClass: UmlClassDetail, relationships: UmlRelationship[] = [], extraClasses: UmlClassDetail[] = []) {
  return render(
    <JointUmlCanvas
      activeTool="select"
      classes={[umlClass, ...extraClasses]}
      isDark={false}
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
});
