import { apiClient } from "./client";
import type {
  AiConversation,
  AiInteractionRequest,
  AiInteractionResponse,
  AiProviderHealth,
  AiActionDecision,
  AiAction,
  AiMessagePage,
  AiProjectSettings,
  AiRecommendation,
  FlutterThemeConfig,
  FlutterThemeSettings,
  MobileDiagramSummary,
  MobileDiagramDetail,
  MobileProjectSummary
} from "../contracts/phase1";

export const phase1Service = {
  async interact(projectId: string, payload: AiInteractionRequest) {
    return (await apiClient.post<AiInteractionResponse>(`/projects/${projectId}/ai/interactions`, payload)).data;
  },
  async aiProviderHealth(projectId: string) {
    return (await apiClient.get<AiProviderHealth>(`/projects/${projectId}/ai/provider-health`)).data;
  },
  async confirmAiAction(projectId: string, actionId: string) {
    return (await apiClient.post<AiActionDecision>(`/projects/${projectId}/ai/actions/${actionId}/confirm`)).data;
  },
  async rejectAiAction(projectId: string, actionId: string) {
    return (await apiClient.post<AiActionDecision>(`/projects/${projectId}/ai/actions/${actionId}/reject`)).data;
  },
  async aiSettings(projectId: string) {
    return (await apiClient.get<AiProjectSettings>(`/projects/${projectId}/ai/settings`)).data;
  },
  async updateAiSettings(projectId: string, payload: Omit<AiProjectSettings, "id" | "project_id" | "created_by_user_id" | "updated_by_user_id" | "created_at" | "updated_at">) {
    return (await apiClient.put<AiProjectSettings>(`/projects/${projectId}/ai/settings`, payload)).data;
  },
  async conversation(projectId: string) {
    return (await apiClient.get<AiConversation>(`/projects/${projectId}/ai/conversation`)).data;
  },
  async conversations(projectId: string) {
    return (await apiClient.get<AiConversation[]>(`/projects/${projectId}/ai/conversations`)).data;
  },
  async createConversation(projectId: string, title = "Nuevo chat") {
    return (await apiClient.post<AiConversation>(
      `/projects/${projectId}/ai/conversations`,
      { title }
    )).data;
  },
  async updateConversation(projectId: string, conversationId: string, title: string) {
    return (await apiClient.patch<AiConversation>(
      `/projects/${projectId}/ai/conversations/${conversationId}`,
      { title }
    )).data;
  },
  async messages(projectId: string, params: { conversation_id?: string; before_sequence?: number; after_sequence?: number; limit?: number } = {}) {
    return (await apiClient.get<AiMessagePage>(`/projects/${projectId}/ai/messages`, { params })).data;
  },
  async actions(projectId: string, params: { conversation_id?: string; status?: string; limit?: number } = {}) {
    const data = (await apiClient.get<unknown>(`/projects/${projectId}/ai/actions`, { params })).data;
    return Array.isArray(data) ? data as AiAction[] : [];
  },
  async recommendations(projectId: string, params: { conversation_id?: string; status?: string; severity?: string; limit?: number } = {}) {
    const data = (await apiClient.get<unknown>(`/projects/${projectId}/ai/recommendations`, { params })).data;
    return Array.isArray(data) ? data as AiRecommendation[] : [];
  },
  async updateRecommendation(
    projectId: string,
    recommendationId: string,
    payload: { status: "accepted" | "dismissed" | "resolved"; resolution_note?: string }
  ) {
    return (await apiClient.patch<AiRecommendation>(
      `/projects/${projectId}/ai/recommendations/${recommendationId}`,
      payload
    )).data;
  },
  async theme(projectId: string) {
    return (await apiClient.get<FlutterThemeSettings>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async saveTheme(projectId: string, config: FlutterThemeConfig, revision: number, presetName?: string) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await apiClient.put<FlutterThemeSettings>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async mobileProjects() {
    return (await apiClient.get<MobileProjectSummary[]>("/mobile/projects")).data;
  },
  async mobileDiagrams(projectId: string) {
    return (await apiClient.get<MobileDiagramSummary[]>(`/mobile/projects/${projectId}/diagrams`)).data;
  },
  async mobileDiagram(diagramId: string) {
    return (await apiClient.get<MobileDiagramDetail>(`/mobile/diagrams/${diagramId}`)).data;
  }
};
