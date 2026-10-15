import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { JointUmlCanvas } from "./JointUmlCanvas";
import type { UmlClassDetail } from "../types/uml";

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

function renderCanvas(umlClass: UmlClassDetail) {
  return render(
    <JointUmlCanvas
      activeTool="select"
      classes={[umlClass]}
      isDark={false}
      onClassClick={vi.fn()}
      onClassMove={vi.fn()}
      onClassRename={vi.fn()}
      onRelationshipClick={vi.fn()}
      pendingSourceId=""
      relationships={[]}
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
});
