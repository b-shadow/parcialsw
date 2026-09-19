import { apiClient } from "../../../core/api/client";
import type { DiagramModel, UmlClass, UmlClassDetail, UmlDiagram, UmlRelationship, UmlValidation, UmlVisualElement } from "../types/uml";

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
    const response = await apiClient.post<{ id: string; name: string }>(`/uml/classes/${classId}/attributes`, payload);
    return response.data;
  },
  async addMethod(classId: string, payload: { name: string; return_type?: string }) {
    const response = await apiClient.post<{ id: string; name: string }>(`/uml/classes/${classId}/methods`, payload);
    return response.data;
  },
  async createRelationship(
    diagramId: string,
    payload: { source_class_id: string; target_class_id: string; relationship_type: string; label?: string }
  ) {
    const response = await apiClient.post<UmlRelationship>(`/uml/diagrams/${diagramId}/relationships`, {
      ...payload,
      direction: "source_to_target",
      metadata_json: {}
    });
    return response.data;
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
  async exportXmi(diagramId: string) {
    const response = await apiClient.get<{ diagram_id: string; file_name: string; content: string }>(`/uml/diagrams/${diagramId}/xmi`);
    return response.data;
  }
};
