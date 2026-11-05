import { clienteApi } from "../../../core/api/cliente";
import type {
  CambioColaboracion,
  Proyecto,
  IntegranteProyecto,
  CandidatoIntegranteProyecto,
  VersionProyecto,
  VistaPreviaRestauracion,
  PaginaActividad,
  ResultadoRestauracionVersion
} from "../types/proyecto";

export const servicioProyectos = {
  async list() {
    const response = await clienteApi.get<Proyecto[]>("/projects");
    return response.data;
  },
  async get(projectId: string) {
    const response = await clienteApi.get<Proyecto>(`/projects/${projectId}`);
    return response.data;
  },
  async create(payload: { name: string; description?: string; settings?: Record<string, unknown> }) {
    const response = await clienteApi.post<Proyecto>("/projects", {
      name: payload.name,
      description: payload.description,
      settings: payload.settings ?? {}
    });
    return response.data;
  },
  async update(projectId: string, payload: Partial<Pick<Proyecto, "name" | "description" | "status" | "settings">>) {
    const response = await clienteApi.patch<Proyecto>(`/projects/${projectId}`, payload);
    return response.data;
  },
  async archive(projectId: string) {
    const response = await clienteApi.delete<Proyecto>(`/projects/${projectId}`);
    return response.data;
  },
  async members(projectId: string) {
    const response = await clienteApi.get<IntegranteProyecto[]>(`/projects/${projectId}/members`);
    return response.data;
  },
  async memberCandidates(projectId: string) {
    const response = await clienteApi.get<CandidatoIntegranteProyecto[]>(
      `/projects/${projectId}/member-candidates`
    );
    return response.data;
  },
  async addMember(projectId: string, payload: { user_id: string; project_role: "ORGANIZADOR" | "EDITOR" }) {
    const response = await clienteApi.post<IntegranteProyecto>(`/projects/${projectId}/members`, payload);
    return response.data;
  },
  async updateMember(projectId: string, memberId: string, payload: { project_role: "ORGANIZADOR" | "EDITOR" }) {
    const response = await clienteApi.patch<IntegranteProyecto>(`/projects/${projectId}/members/${memberId}`, payload);
    return response.data;
  },
  async removeMember(projectId: string, memberId: string) {
    await clienteApi.delete(`/projects/${projectId}/members/${memberId}`);
  },
  async saveVersion(projectId: string, payload: { name: string; description?: string; expected_project_revision?: number; allow_duplicate?: boolean }, idempotencyKey = crypto.randomUUID()) {
    const response = await clienteApi.post<VersionProyecto>(`/projects/${projectId}/versions`, payload, {
      headers: { "Idempotency-Key": idempotencyKey }
    });
    return response.data;
  },
  async versions(projectId: string) {
    const response = await clienteApi.get<VersionProyecto[]>(`/projects/${projectId}/versions`);
    return response.data;
  },
  async restorePreview(projectId: string, versionId: string) {
    const response = await clienteApi.get<VistaPreviaRestauracion>(
      `/projects/${projectId}/versions/${versionId}/restore-preview`
    );
    return response.data;
  },
  async restoreVersion(projectId: string, versionId: string, expectedProjectRevision?: number, idempotencyKey = crypto.randomUUID()) {
    const response = await clienteApi.post<ResultadoRestauracionVersion>(
      `/projects/${projectId}/versions/${versionId}/restore`,
      { expected_project_revision: expectedProjectRevision },
      { headers: { "Idempotency-Key": idempotencyKey } }
    );
    return response.data;
  },
  async activity(projectId: string, beforeSequence?: number, limit = 50) {
    const response = await clienteApi.get<PaginaActividad>(`/projects/${projectId}/activity`, {
      params: { before_sequence: beforeSequence, limit }
    });
    return response.data;
  },
  async changes(projectId: string, limit = 100, afterSequence?: number) {
    const response = await clienteApi.get<CambioColaboracion[]>(`/projects/${projectId}/changes`, {
      params: { limit, after_sequence: afterSequence }
    });
    return response.data;
  }
};
