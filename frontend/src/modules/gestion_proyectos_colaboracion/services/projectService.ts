import { apiClient } from "../../../core/api/client";
import type { Project, ProjectMember, ProjectVersion } from "../types/project";

export const projectService = {
  async list() {
    const response = await apiClient.get<Project[]>("/projects");
    return response.data;
  },
  async get(projectId: string) {
    const response = await apiClient.get<Project>(`/projects/${projectId}`);
    return response.data;
  },
  async create(payload: { name: string; description?: string; settings?: Record<string, unknown> }) {
    const response = await apiClient.post<Project>("/projects", {
      name: payload.name,
      description: payload.description,
      settings: payload.settings ?? {}
    });
    return response.data;
  },
  async update(projectId: string, payload: Partial<Pick<Project, "name" | "description" | "status" | "settings">>) {
    const response = await apiClient.patch<Project>(`/projects/${projectId}`, payload);
    return response.data;
  },
  async archive(projectId: string) {
    const response = await apiClient.delete<Project>(`/projects/${projectId}`);
    return response.data;
  },
  async members(projectId: string) {
    const response = await apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`);
    return response.data;
  },
  async addMember(projectId: string, payload: { user_id: string; project_role: "ORGANIZADOR" | "EDITOR" }) {
    const response = await apiClient.post<ProjectMember>(`/projects/${projectId}/members`, payload);
    return response.data;
  },
  async updateMember(projectId: string, memberId: string, payload: { project_role: "ORGANIZADOR" | "EDITOR" }) {
    const response = await apiClient.patch<ProjectMember>(`/projects/${projectId}/members/${memberId}`, payload);
    return response.data;
  },
  async removeMember(projectId: string, memberId: string) {
    await apiClient.delete(`/projects/${projectId}/members/${memberId}`);
  },
  async saveVersion(projectId: string, payload: { name: string; description?: string; snapshot: Record<string, unknown> }) {
    const response = await apiClient.post<ProjectVersion>(`/projects/${projectId}/versions`, payload);
    return response.data;
  }
};
