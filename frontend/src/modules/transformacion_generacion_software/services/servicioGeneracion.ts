import { clienteApi } from "../../../core/api/cliente";
import type {
  GeneracionCoordinada,
  ConfiguracionTemaFlutter,
  EntradaTemaFlutter,
  CargaGeneracionFrontend,
  BackendGenerado,
  FrontendGenerado,
  VerificacionPreviaGeneracion,
  TemaFlutterPredefinido,
  AjustesTemaFlutter,
  DiagnosticoTema,
  ManifiestoUI,
  Transformacion
} from "../types/generacion";

export const servicioGeneracion = {
  async transform(payload: { diagram_id: string; target_platform: "spring_boot" | "flutter" | "full_stack" }) {
    const response = await clienteApi.post<Transformacion>("/generation/transformations", payload);
    return response.data;
  },
  async springBoot(payload: { transformation_id: string; name: string; version_label: string }) {
    const response = await clienteApi.post<BackendGenerado>("/generation/spring-boot", payload);
    return response.data;
  },
  async backends(projectId: string) {
    return (await clienteApi.get<BackendGenerado[]>(
      `/generation/projects/${projectId}/spring-boot`
    )).data;
  },
  async flutter(payload: CargaGeneracionFrontend) {
    const response = await clienteApi.post<FrontendGenerado>("/generation/flutter", payload);
    return response.data;
  },
  async frontends(projectId: string) {
    return (await clienteApi.get<FrontendGenerado[]>(
      `/generation/projects/${projectId}/flutter`
    )).data;
  },
  async downloadSpringBoot(backendId: string) {
    const response = await clienteApi.get<Blob>(`/generation/spring-boot/${backendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async downloadFlutter(frontendId: string) {
    const response = await clienteApi.get<Blob>(`/generation/flutter/${frontendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async preflightCoordinated(payload: {
    transformation_id: string;
    name: string;
    theme_config: EntradaTemaFlutter;
  }) {
    const response = await clienteApi.post<VerificacionPreviaGeneracion>("/generation/coordinated/preflight", payload);
    return response.data;
  },
  async coordinated(payload: {
    transformation_id: string;
    name: string;
    client_request_id: string;
    api_base_url: string;
    verify: boolean;
    allow_unverified: boolean;
    theme_config: EntradaTemaFlutter;
  }) {
    const response = await clienteApi.post<GeneracionCoordinada>("/generation/coordinated", payload);
    return response.data;
  },
  async downloadCoordinated(generationId: string) {
    const response = await clienteApi.get<Blob>(`/generation/coordinated/${generationId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async getTheme(projectId: string) {
    return (await clienteApi.get<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async validateTheme(projectId: string, config: ConfiguracionTemaFlutter) {
    return (await clienteApi.post<{ theme: ConfiguracionTemaFlutter; diagnostics: DiagnosticoTema[]; normalized_fields: string[]; valid: boolean }>(`/projects/${projectId}/flutter-theme/validate`, { config })).data;
  },
  async saveTheme(projectId: string, config: ConfiguracionTemaFlutter, revision: number, presetName?: string | null) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await clienteApi.put<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async presets(projectId: string) {
    return (await clienteApi.get<TemaFlutterPredefinido[]>(`/projects/${projectId}/flutter-theme/presets`)).data;
  },
  async createPreset(projectId: string, name: string, config: ConfiguracionTemaFlutter) {
    return (await clienteApi.post<TemaFlutterPredefinido>(`/projects/${projectId}/flutter-theme/presets`, { name, config })).data;
  },
  async deletePreset(projectId: string, presetId: string) {
    await clienteApi.delete(`/projects/${projectId}/flutter-theme/presets/${presetId}`);
  },
  async uiManifest(transformationId: string) {
    return (await clienteApi.get<ManifiestoUI>(`/generation/transformations/${transformationId}/ui-manifest`)).data;
  }
};
