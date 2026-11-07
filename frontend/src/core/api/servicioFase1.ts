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
  async interactuar(projectId: string, payload: SolicitudInteraccionIA) {
    return (await clienteApi.post<RespuestaInteraccionIA>(`/projects/${projectId}/ai/interactions`, payload)).data;
  },
  async estadoProveedorIA(projectId: string) {
    return (await clienteApi.get<EstadoProveedorIA>(`/projects/${projectId}/ai/provider-health`)).data;
  },
  async confirmarAccionIA(projectId: string, actionId: string) {
    return (await clienteApi.post<DecisionAccionIA>(`/projects/${projectId}/ai/actions/${actionId}/confirm`)).data;
  },
  async rechazarAccionIA(projectId: string, actionId: string) {
    return (await clienteApi.post<DecisionAccionIA>(`/projects/${projectId}/ai/actions/${actionId}/reject`)).data;
  },
  async configuracionIA(projectId: string) {
    return (await clienteApi.get<ConfiguracionIAProyecto>(`/projects/${projectId}/ai/settings`)).data;
  },
  async actualizarConfiguracionIA(projectId: string, payload: Omit<ConfiguracionIAProyecto, "id" | "project_id" | "created_by_user_id" | "updated_by_user_id" | "created_at" | "updated_at">) {
    return (await clienteApi.put<ConfiguracionIAProyecto>(`/projects/${projectId}/ai/settings`, payload)).data;
  },
  async obtenerConversacion(projectId: string) {
    return (await clienteApi.get<ConversacionIA>(`/projects/${projectId}/ai/conversation`)).data;
  },
  async listarConversaciones(projectId: string) {
    return (await clienteApi.get<ConversacionIA[]>(`/projects/${projectId}/ai/conversations`)).data;
  },
  async crearConversacion(projectId: string, title = "Nuevo chat") {
    return (await clienteApi.post<ConversacionIA>(
      `/projects/${projectId}/ai/conversations`,
      { title }
    )).data;
  },
  async actualizarConversacion(projectId: string, conversationId: string, title: string) {
    return (await clienteApi.patch<ConversacionIA>(
      `/projects/${projectId}/ai/conversations/${conversationId}`,
      { title }
    )).data;
  },
  async listarMensajes(projectId: string, params: { conversation_id?: string; before_sequence?: number; after_sequence?: number; limit?: number } = {}) {
    return (await clienteApi.get<PaginaMensajesIA>(`/projects/${projectId}/ai/messages`, { params })).data;
  },
  async listarAcciones(projectId: string, params: { conversation_id?: string; status?: string; limit?: number } = {}) {
    const data = (await clienteApi.get<unknown>(`/projects/${projectId}/ai/actions`, { params })).data;
    return Array.isArray(data) ? data as AccionIA[] : [];
  },
  async listarRecomendaciones(projectId: string, params: { conversation_id?: string; status?: string; severity?: string; limit?: number } = {}) {
    const data = (await clienteApi.get<unknown>(`/projects/${projectId}/ai/recommendations`, { params })).data;
    return Array.isArray(data) ? data as RecomendacionIA[] : [];
  },
  async actualizarRecomendacion(
    projectId: string,
    recommendationId: string,
    payload: { status: "accepted" | "dismissed" | "resolved"; resolution_note?: string }
  ) {
    return (await clienteApi.patch<RecomendacionIA>(
      `/projects/${projectId}/ai/recommendations/${recommendationId}`,
      payload
    )).data;
  },
  async obtenerTema(projectId: string) {
    return (await clienteApi.get<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async guardarTema(projectId: string, config: ConfiguracionTemaFlutter, revision: number, presetName?: string) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await clienteApi.put<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async proyectosMoviles() {
    return (await clienteApi.get<ResumenProyectoMovil[]>("/mobile/projects")).data;
  },
  async diagramasMoviles(projectId: string) {
    return (await clienteApi.get<ResumenDiagramaMovil[]>(`/mobile/projects/${projectId}/diagrams`)).data;
  },
  async diagramaMovil(diagramId: string) {
    return (await clienteApi.get<DetalleDiagramaMovil>(`/mobile/diagrams/${diagramId}`)).data;
  }
};
