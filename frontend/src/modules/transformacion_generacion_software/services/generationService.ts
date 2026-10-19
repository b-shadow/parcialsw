import { apiClient } from "../../../core/api/client";
import type {
  CoordinatedGeneration,
  FlutterThemeConfig,
  FlutterThemeInput,
  FrontendGenerationPayload,
  GeneratedBackend,
  GeneratedFrontend,
  GenerationPreflight,
  FlutterThemePreset,
  FlutterThemeSettings,
  ThemeDiagnostic,
  UiManifest,
  Transformation
} from "../types/generation";

export const generationService = {
  async transform(payload: { diagram_id: string; target_platform: "spring_boot" | "flutter" | "full_stack" }) {
    const response = await apiClient.post<Transformation>("/generation/transformations", payload);
    return response.data;
  },
  async springBoot(payload: { transformation_id: string; name: string; version_label: string }) {
    const response = await apiClient.post<GeneratedBackend>("/generation/spring-boot", payload);
    return response.data;
  },
  async backends(projectId: string) {
    return (await apiClient.get<GeneratedBackend[]>(
      `/generation/projects/${projectId}/spring-boot`
    )).data;
  },
  async flutter(payload: FrontendGenerationPayload) {
    const response = await apiClient.post<GeneratedFrontend>("/generation/flutter", payload);
    return response.data;
  },
  async frontends(projectId: string) {
    return (await apiClient.get<GeneratedFrontend[]>(
      `/generation/projects/${projectId}/flutter`
    )).data;
  },
  async downloadSpringBoot(backendId: string) {
    const response = await apiClient.get<Blob>(`/generation/spring-boot/${backendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async downloadFlutter(frontendId: string) {
    const response = await apiClient.get<Blob>(`/generation/flutter/${frontendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async preflightCoordinated(payload: {
    transformation_id: string;
    name: string;
    theme_config: FlutterThemeInput;
  }) {
    const response = await apiClient.post<GenerationPreflight>("/generation/coordinated/preflight", payload);
    return response.data;
  },
  async coordinated(payload: {
    transformation_id: string;
    name: string;
    client_request_id: string;
    api_base_url: string;
    verify: boolean;
    allow_unverified: boolean;
    theme_config: FlutterThemeInput;
  }) {
    const response = await apiClient.post<CoordinatedGeneration>("/generation/coordinated", payload);
    return response.data;
  },
  async downloadCoordinated(generationId: string) {
    const response = await apiClient.get<Blob>(`/generation/coordinated/${generationId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async getTheme(projectId: string) {
    return (await apiClient.get<FlutterThemeSettings>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async validateTheme(projectId: string, config: FlutterThemeConfig) {
    return (await apiClient.post<{ theme: FlutterThemeConfig; diagnostics: ThemeDiagnostic[]; normalized_fields: string[]; valid: boolean }>(`/projects/${projectId}/flutter-theme/validate`, { config })).data;
  },
  async saveTheme(projectId: string, config: FlutterThemeConfig, revision: number, presetName?: string | null) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await apiClient.put<FlutterThemeSettings>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async presets(projectId: string) {
    return (await apiClient.get<FlutterThemePreset[]>(`/projects/${projectId}/flutter-theme/presets`)).data;
  },
  async createPreset(projectId: string, name: string, config: FlutterThemeConfig) {
    return (await apiClient.post<FlutterThemePreset>(`/projects/${projectId}/flutter-theme/presets`, { name, config })).data;
  },
  async deletePreset(projectId: string, presetId: string) {
    await apiClient.delete(`/projects/${projectId}/flutter-theme/presets/${presetId}`);
  },
  async uiManifest(transformationId: string) {
    return (await apiClient.get<UiManifest>(`/generation/transformations/${transformationId}/ui-manifest`)).data;
  }
};
