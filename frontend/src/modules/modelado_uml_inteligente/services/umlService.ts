import { apiClient } from "../../../core/api/client";
import type {
  DiagramModel,
  UmlAttribute,
  UmlClass,
  UmlClassDetail,
  UmlDiagram,
  UmlMethod,
  UmlRelationship,
  UmlValidation,
  UmlVisualElement
} from "../types/uml";

export const umlService = {
  async createDiagram(payload: { project_id: string; name: string; description?: string }) {
    const response = await apiClient.post<UmlDiagram>("/uml/diagrams", {
      ...payload,
      metadata_json: {}
    });
    return response.data;
  },
  async listDiagrams(projectId: string) {
    const response = await apiClient.get<UmlDiagram[]>(`/uml/projects/${projectId}/diagrams`);
    return response.data;
  },
  async deleteDiagram(diagramId: string) {
    await apiClient.delete(`/uml/diagrams/${diagramId}`);
  },
  async createClass(
    diagramId: string,
    payload: { name: string; position_x: number; position_y: number; description?: string }
  ) {
    const response = await apiClient.post<UmlClass>(`/uml/diagrams/${diagramId}/classes`, {
      name: payload.name,
      position_x: payload.position_x,
      position_y: payload.position_y,
      description: payload.description,
      visibility: "public",
      element_type: "class",
      metadata_json: { attributes: [], methods: [] }
    });
    return response.data;
  },
  async listClasses(diagramId: string) {
    const response = await apiClient.get<UmlClass[]>(`/uml/diagrams/${diagramId}/classes`);
    return response.data;
  },
  async getDiagramModel(diagramId: string) {
    const response = await apiClient.get<DiagramModel>(`/uml/diagrams/${diagramId}/model`);
    return response.data;
  },
  async updateClass(classId: string, payload: Partial<Pick<UmlClass, "name" | "visibility" | "description" | "stereotype">>) {
    const response = await apiClient.patch<UmlClassDetail>(`/uml/classes/${classId}`, payload);
    return response.data;
  },
  async deleteClass(classId: string) {
    await apiClient.delete(`/uml/classes/${classId}`);
  },
  async moveElement(diagramId: string, payload: { element_type: "class" | "relationship"; element_id: string; position_x: number; position_y: number }) {
    const response = await apiClient.patch<UmlVisualElement>(`/uml/diagrams/${diagramId}/visual-elements`, payload);
    return response.data;
  },
  async addAttribute(classId: string, payload: { name: string; data_type: string }) {
    const response = await apiClient.post<UmlAttribute>(`/uml/classes/${classId}/attributes`, payload);
    return response.data;
  },
  async updateAttribute(attributeId: string, payload: Partial<Pick<UmlAttribute, "name" | "data_type" | "visibility" | "initial_value" | "multiplicity" | "is_required" | "order_index" | "constraints">>) {
    const response = await apiClient.patch<UmlAttribute>(`/uml/attributes/${attributeId}`, payload);
    return response.data;
  },
  async deleteAttribute(attributeId: string) {
    await apiClient.delete(`/uml/attributes/${attributeId}`);
  },
  async addMethod(classId: string, payload: { name: string; return_type?: string; visibility?: string }) {
    const response = await apiClient.post<UmlMethod>(`/uml/classes/${classId}/methods`, payload);
    return response.data;
  },
  async updateMethod(methodId: string, payload: Partial<Pick<UmlMethod, "name" | "return_type" | "visibility" | "order_index" | "metadata_json">>) {
    const response = await apiClient.patch<UmlMethod>(`/uml/methods/${methodId}`, payload);
    return response.data;
  },
  async deleteMethod(methodId: string) {
    await apiClient.delete(`/uml/methods/${methodId}`);
  },
  async createRelationship(
    diagramId: string,
    payload: {
      source_class_id: string;
      target_class_id: string;
      relationship_type: string;
      label?: string;
      source_cardinality?: string | null;
      target_cardinality?: string | null;
      metadata_json?: Record<string, unknown>;
    }
  ) {
    const response = await apiClient.post<UmlRelationship>(`/uml/diagrams/${diagramId}/relationships`, {
      ...payload,
      direction: "source_to_target",
      metadata_json: payload.metadata_json ?? {}
    });
    return response.data;
  },
  async updateRelationship(
    relationshipId: string,
    payload: Partial<
      Pick<UmlRelationship, "relationship_type" | "label" | "source_cardinality" | "target_cardinality" | "direction" | "metadata_json">
    >
  ) {
    const response = await apiClient.patch<UmlRelationship>(`/uml/relationships/${relationshipId}`, payload);
    return response.data;
  },
  async deleteRelationship(relationshipId: string) {
    await apiClient.delete(`/uml/relationships/${relationshipId}`);
  },
  async validate(diagramId: string) {
    const response = await apiClient.post<UmlValidation>(`/uml/diagrams/${diagramId}/validate`);
    return response.data;
  },
  async generate(payload: { project_id: string; name: string; prompt: string; source_type: "text" | "voice" | "image" }) {
    const response = await apiClient.post<UmlDiagram>("/uml/generate", payload);
    return response.data;
  },
  async importXmi(payload: { project_id: string; name: string; content: string; file_name: string }) {
    const response = await apiClient.post<UmlDiagram>("/uml/xmi/import", payload);
    return response.data;
  },
  async importXmiIntoDiagram(diagramId: string, payload: { project_id: string; name: string; content: string; file_name: string }) {
    const response = await apiClient.post<UmlDiagram>(`/uml/diagrams/${diagramId}/xmi/import`, payload);
    return response.data;
  },
  async exportXmi(diagramId: string) {
    const response = await apiClient.get<{ diagram_id: string; file_name: string; content: string }>(`/uml/diagrams/${diagramId}/xmi`);
    return response.data;
  }
};
