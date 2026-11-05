import { clienteApi } from "./cliente";
import type {
  ConversacionIA,
  SolicitudInteraccionIA,
  RespuestaInteraccionIA,
  EstadoProveedorIA,
  DecisionAccionIA,
  AccionIA,
  PaginaMensajesIA,
  ConfiguracionIAProyecto,
  RecomendacionIA,
  ConfiguracionTemaFlutter,
  AjustesTemaFlutter,
  ResumenDiagramaMovil,
  DetalleDiagramaMovil,
  ResumenProyectoMovil
} from "../contracts/phase1";

export const servicioFase1 = {
  async interact(projectId: string, payload: SolicitudInteraccionIA) {
    return (await clienteApi.post<RespuestaInteraccionIA>(`/projects/${projectId}/ai/interactions`, payload)).data;
  },
  async aiProviderHealth(projectId: string) {
    return (await clienteApi.get<EstadoProveedorIA>(`/projects/${projectId}/ai/provider-health`)).data;
  },
  async confirmAiAction(projectId: string, actionId: string) {
    return (await clienteApi.post<DecisionAccionIA>(`/projects/${projectId}/ai/actions/${actionId}/confirm`)).data;
  },
  async rejectAiAction(projectId: string, actionId: string) {
    return (await clienteApi.post<DecisionAccionIA>(`/projects/${projectId}/ai/actions/${actionId}/reject`)).data;
  },
  async aiSettings(projectId: string) {
    return (await clienteApi.get<ConfiguracionIAProyecto>(`/projects/${projectId}/ai/settings`)).data;
  },
  async updateAiSettings(projectId: string, payload: Omit<ConfiguracionIAProyecto, "id" | "project_id" | "created_by_user_id" | "updated_by_user_id" | "created_at" | "updated_at">) {
    return (await clienteApi.put<ConfiguracionIAProyecto>(`/projects/${projectId}/ai/settings`, payload)).data;
  },
  async conversation(projectId: string) {
    return (await clienteApi.get<ConversacionIA>(`/projects/${projectId}/ai/conversation`)).data;
  },
  async conversations(projectId: string) {
    return (await clienteApi.get<ConversacionIA[]>(`/projects/${projectId}/ai/conversations`)).data;
  },
  async createConversation(projectId: string, title = "Nuevo chat") {
    return (await clienteApi.post<ConversacionIA>(
      `/projects/${projectId}/ai/conversations`,
      { title }
    )).data;
  },
  async updateConversation(projectId: string, conversationId: string, title: string) {
    return (await clienteApi.patch<ConversacionIA>(
      `/projects/${projectId}/ai/conversations/${conversationId}`,
      { title }
    )).data;
  },
  async messages(projectId: string, params: { conversation_id?: string; before_sequence?: number; after_sequence?: number; limit?: number } = {}) {
    return (await clienteApi.get<PaginaMensajesIA>(`/projects/${projectId}/ai/messages`, { params })).data;
  },
  async actions(projectId: string, params: { conversation_id?: string; status?: string; limit?: number } = {}) {
    const data = (await clienteApi.get<unknown>(`/projects/${projectId}/ai/actions`, { params })).data;
    return Array.isArray(data) ? data as AccionIA[] : [];
  },
  async recommendations(projectId: string, params: { conversation_id?: string; status?: string; severity?: string; limit?: number } = {}) {
    const data = (await clienteApi.get<unknown>(`/projects/${projectId}/ai/recommendations`, { params })).data;
    return Array.isArray(data) ? data as RecomendacionIA[] : [];
  },
  async updateRecommendation(
    projectId: string,
    recommendationId: string,
    payload: { status: "accepted" | "dismissed" | "resolved"; resolution_note?: string }
  ) {
    return (await clienteApi.patch<RecomendacionIA>(
      `/projects/${projectId}/ai/recommendations/${recommendationId}`,
      payload
    )).data;
  },
  async theme(projectId: string) {
    return (await clienteApi.get<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async saveTheme(projectId: string, config: ConfiguracionTemaFlutter, revision: number, presetName?: string) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await clienteApi.put<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async mobileProjects() {
    return (await clienteApi.get<ResumenProyectoMovil[]>("/mobile/projects")).data;
  },
  async mobileDiagrams(projectId: string) {
    return (await clienteApi.get<ResumenDiagramaMovil[]>(`/mobile/projects/${projectId}/diagrams`)).data;
  },
  async mobileDiagram(diagramId: string) {
    return (await clienteApi.get<DetalleDiagramaMovil>(`/mobile/diagrams/${diagramId}`)).data;
  }
};
