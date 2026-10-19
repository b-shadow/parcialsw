import { describe, expect, it, vi } from "vitest";

import { apiClient } from "../../../core/api/client";
import { umlService } from "./umlService";
import type { UmlClass, UmlClassDetail, UmlRelationship } from "../types/uml";

vi.mock("../../../core/api/client", () => ({
  apiClient: {
    post: vi.fn(),
    patch: vi.fn()
  }
}));

const mockedApiClient = vi.mocked(apiClient);

function classDetail(patch: Partial<UmlClassDetail> & Pick<UmlClassDetail, "id" | "name">): UmlClassDetail {
  return {
    id: patch.id,
    diagram_id: patch.diagram_id ?? "diagram-1",
    name: patch.name,
    visibility: patch.visibility ?? "public",
    element_type: patch.element_type ?? "class",
    stereotype: patch.stereotype ?? null,
    description: patch.description ?? null,
    metadata_json: patch.metadata_json ?? {},
    attributes: patch.attributes ?? [],
    methods: patch.methods ?? [],
    visual: patch.visual ?? null
  };
}

describe("umlService.applyAiModificationToDiagram", () => {
  it("fusiona lo detectado con el diagrama actual sin reemplazar sus clases", async () => {
    const createdClass: UmlClass = {
      id: "class-perfil",
      diagram_id: "diagram-1",
      name: "Perfil",
      visibility: "public",
      element_type: "class",
      stereotype: "entity",
      description: null,
      metadata_json: { attributes: [], methods: [] }
    };
    const createdRelationship: UmlRelationship = {
      id: "relationship-1",
      diagram_id: "diagram-1",
      source_class_id: "class-perfil",
      target_class_id: "class-usuario",
      relationship_type: "association",
      source_cardinality: "1",
      target_cardinality: "1",
      direction: "source_to_target",
      label: "asocia",
      metadata_json: {}
    };
    mockedApiClient.post.mockImplementation(async (url: string, payload?: unknown) => {
      if (url === "/uml/diagrams/diagram-1/classes") {
        expect(payload).toMatchObject({
          name: "Perfil",
          position_x: expect.any(Number),
          position_y: expect.any(Number)
        });
        return { data: createdClass };
      }
      if (url === "/uml/classes/class-perfil/attributes") {
        return { data: { id: `attr-${mockedApiClient.post.mock.calls.length}`, class_id: "class-perfil", ...(payload as object) } };
      }
      if (url === "/uml/diagrams/diagram-1/relationships") {
        expect(payload).toMatchObject({
          source_class_id: "class-perfil",
          target_class_id: "class-usuario",
          relationship_type: "association",
          source_cardinality: "1",
          target_cardinality: "1"
        });
        return { data: createdRelationship };
      }
      throw new Error(`Unexpected POST ${url}`);
    });

    await umlService.applyAiModificationToDiagram({
      diagramId: "diagram-1",
      classes: [
        classDetail({
          id: "class-usuario",
          name: "Usuario",
          attributes: [
            {
              id: "attribute-usuario-id",
              class_id: "class-usuario",
              name: "id",
              data_type: "UUID",
              visibility: "private",
              initial_value: null,
              multiplicity: null,
              is_required: true,
              order_index: 0,
              constraints: {}
            }
          ]
        })
      ],
      relationships: [],
      result: {
        engine: "local-offline",
        confidence: 0.88,
        observations: [],
        knowledge_context: [],
        classes: [
          {
            name: "Usuario",
            attributes: [{ name: "id", data_type: "UUID", visibility: "private", is_required: true }],
            methods: []
          },
          {
            name: "Perfil",
            stereotype: "entity",
            attributes: [
              { name: "id", data_type: "UUID", visibility: "private", is_required: true },
              { name: "biografia", data_type: "String", visibility: "private", is_required: false }
            ],
            methods: []
          }
        ],
        relationships: [
          {
            source: "Perfil",
            target: "Usuario",
            relationship_type: "association",
            label: "asocia",
            source_cardinality: "1",
            target_cardinality: "1",
            metadata_json: {}
          }
        ]
      }
    });

    expect(mockedApiClient.post).toHaveBeenCalledWith(
      "/uml/diagrams/diagram-1/classes",
      expect.objectContaining({ name: "Perfil" })
    );
    expect(mockedApiClient.post).not.toHaveBeenCalledWith(
      "/uml/diagrams/diagram-1/classes",
      expect.objectContaining({ name: "Usuario" })
    );
    expect(mockedApiClient.post).not.toHaveBeenCalledWith(
      "/uml/classes/class-usuario/attributes",
      expect.anything()
    );
    expect(mockedApiClient.post).toHaveBeenCalledWith(
      "/uml/classes/class-perfil/attributes",
      expect.objectContaining({ name: "id", data_type: "UUID" })
    );
    expect(mockedApiClient.post).toHaveBeenCalledWith(
      "/uml/classes/class-perfil/attributes",
      expect.objectContaining({ name: "biografia", data_type: "String" })
    );
    expect(mockedApiClient.post).toHaveBeenCalledWith(
      "/uml/diagrams/diagram-1/relationships",
      expect.objectContaining({
        source_class_id: "class-perfil",
        target_class_id: "class-usuario",
        source_cardinality: "1",
        target_cardinality: "1"
      })
    );
    expect(mockedApiClient.patch).not.toHaveBeenCalled();
  });
});
