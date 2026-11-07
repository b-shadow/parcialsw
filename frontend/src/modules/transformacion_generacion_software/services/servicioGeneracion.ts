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
  async transformar(payload: { diagram_id: string; target_platform: "spring_boot" | "flutter" | "full_stack" }) {
    const response = await clienteApi.post<Transformacion>("/generation/transformations", payload);
    return response.data;
  },
  async generarSpringBoot(payload: { transformation_id: string; name: string; version_label: string }) {
    const response = await clienteApi.post<BackendGenerado>("/generation/spring-boot", payload);
    return response.data;
  },
  async listarBackends(projectId: string) {
    return (await clienteApi.get<BackendGenerado[]>(
      `/generation/projects/${projectId}/spring-boot`
    )).data;
  },
  async generarFlutter(payload: CargaGeneracionFrontend) {
    const response = await clienteApi.post<FrontendGenerado>("/generation/flutter", payload);
    return response.data;
  },
  async listarFrontends(projectId: string) {
    return (await clienteApi.get<FrontendGenerado[]>(
      `/generation/projects/${projectId}/flutter`
    )).data;
  },
  async descargarSpringBoot(backendId: string) {
    const response = await clienteApi.get<Blob>(`/generation/spring-boot/${backendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async descargarFlutter(frontendId: string) {
    const response = await clienteApi.get<Blob>(`/generation/flutter/${frontendId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async verificarGeneracionCoordinada(payload: {
    transformation_id: string;
    name: string;
    theme_config: EntradaTemaFlutter;
  }) {
    const response = await clienteApi.post<VerificacionPreviaGeneracion>("/generation/coordinated/preflight", payload);
    return response.data;
  },
  async generarCoordinado(payload: {
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
  async descargarCoordinado(generationId: string) {
    const response = await clienteApi.get<Blob>(`/generation/coordinated/${generationId}/download`, {
      responseType: "blob"
    });
    return response.data;
  },
  async obtenerTema(projectId: string) {
    return (await clienteApi.get<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`)).data;
  },
  async validarTema(projectId: string, config: ConfiguracionTemaFlutter) {
    return (await clienteApi.post<{ theme: ConfiguracionTemaFlutter; diagnostics: DiagnosticoTema[]; normalized_fields: string[]; valid: boolean }>(`/projects/${projectId}/flutter-theme/validate`, { config })).data;
  },
  async guardarTema(projectId: string, config: ConfiguracionTemaFlutter, revision: number, presetName?: string | null) {
    const headers = revision === 0 ? { "If-None-Match": "*" } : { "If-Match": `"flutter-theme-revision-${revision}"` };
    return (await clienteApi.put<AjustesTemaFlutter>(`/projects/${projectId}/flutter-theme`, { config, preset_name: presetName ?? null }, { headers })).data;
  },
  async listarPreajustes(projectId: string) {
    return (await clienteApi.get<TemaFlutterPredefinido[]>(`/projects/${projectId}/flutter-theme/presets`)).data;
  },
  async crearPreajuste(projectId: string, name: string, config: ConfiguracionTemaFlutter) {
    return (await clienteApi.post<TemaFlutterPredefinido>(`/projects/${projectId}/flutter-theme/presets`, { name, config })).data;
  },
  async eliminarPreajuste(projectId: string, presetId: string) {
    await clienteApi.delete(`/projects/${projectId}/flutter-theme/presets/${presetId}`);
  },
  async manifiestoInterfaz(transformationId: string) {
    return (await clienteApi.get<ManifiestoUI>(`/generation/transformations/${transformationId}/ui-manifest`)).data;
  }
};
