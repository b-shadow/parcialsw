import { apiClient } from "../../../core/api/client";
import type { GeneratedBackend, GeneratedFrontend, Transformation } from "../types/generation";

export const generationService = {
  async transform(payload: { diagram_id: string; target_platform: "spring_boot" | "flutter" | "full_stack" }) {
    const response = await apiClient.post<Transformation>("/generation/transformations", payload);
    return response.data;
  },
  async springBoot(payload: { transformation_id: string; name: string; version_label: string }) {
    const response = await apiClient.post<GeneratedBackend>("/generation/spring-boot", payload);
    return response.data;
  },
  async flutter(payload: { transformation_id: string; name: string; version_label: string; backend_id?: string }) {
    const response = await apiClient.post<GeneratedFrontend>("/generation/flutter", payload);
    return response.data;
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
  }
};
