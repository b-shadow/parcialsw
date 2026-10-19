import { apiClient } from "../../../core/api/client";
import type {
  CollaborationChange,
  Project,
  ProjectMember,
  ProjectMemberCandidate,
  ProjectVersion,
  RestorePreview,
  ActivityPage,
  VersionRestoreResult
} from "../types/project";

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
  async memberCandidates(projectId: string) {
    const response = await apiClient.get<ProjectMemberCandidate[]>(
      `/projects/${projectId}/member-candidates`
    );
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
  async saveVersion(projectId: string, payload: { name: string; description?: string; expected_project_revision?: number; allow_duplicate?: boolean }, idempotencyKey = crypto.randomUUID()) {
    const response = await apiClient.post<ProjectVersion>(`/projects/${projectId}/versions`, payload, {
      headers: { "Idempotency-Key": idempotencyKey }
    });
    return response.data;
  },
  async versions(projectId: string) {
    const response = await apiClient.get<ProjectVersion[]>(`/projects/${projectId}/versions`);
    return response.data;
  },
  async restorePreview(projectId: string, versionId: string) {
    const response = await apiClient.get<RestorePreview>(
      `/projects/${projectId}/versions/${versionId}/restore-preview`
    );
    return response.data;
  },
  async restoreVersion(projectId: string, versionId: string, expectedProjectRevision?: number, idempotencyKey = crypto.randomUUID()) {
    const response = await apiClient.post<VersionRestoreResult>(
      `/projects/${projectId}/versions/${versionId}/restore`,
      { expected_project_revision: expectedProjectRevision },
      { headers: { "Idempotency-Key": idempotencyKey } }
    );
    return response.data;
  },
  async activity(projectId: string, beforeSequence?: number, limit = 50) {
    const response = await apiClient.get<ActivityPage>(`/projects/${projectId}/activity`, {
      params: { before_sequence: beforeSequence, limit }
    });
    return response.data;
  },
  async changes(projectId: string, limit = 100, afterSequence?: number) {
    const response = await apiClient.get<CollaborationChange[]>(`/projects/${projectId}/changes`, {
      params: { limit, after_sequence: afterSequence }
    });
    return response.data;
  }
};
