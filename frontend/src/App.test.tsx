import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import { JointUmlCanvas } from "./modules/modelado_uml_inteligente/components/JointUmlCanvas";

describe("App", () => {
  it("renderiza el acceso como primera ruta cuando no hay token", () => {
    window.localStorage.clear();
    render(<App />);
    expect(screen.getByRole("heading", { name: /bienvenido/i })).toBeInTheDocument();
  });

  it("dibuja una clase UML cuando el modelo contiene clases", () => {
    render(
      <JointUmlCanvas
        activeTool="select"
        classes={[
          {
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
            visual: {
              id: "visual-1",
              diagram_id: "diagram-1",
              element_type: "class",
              element_id: "class-1",
              position_x: 90,
              position_y: 90,
              width: null,
              height: null,
              style: {}
            }
          }
        ]}
        isDark={false}
        onClassClick={() => undefined}
        onClassMove={() => undefined}
        onClassRename={() => undefined}
        onRelationshipClick={() => undefined}
        pendingSourceId=""
        relationships={[]}
        selectedClassId={null}
        selectedRelationshipId={null}
      />
    );

    expect(screen.getByDisplayValue("Cliente")).toBeInTheDocument();
  });
});
