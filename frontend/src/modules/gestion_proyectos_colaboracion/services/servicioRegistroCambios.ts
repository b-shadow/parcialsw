import { clienteApi } from "../../../core/api/cliente";
import type { PaginaRegistroCambios } from "../../../core/contracts/mejoras2p";

export type ParametrosRegistroCambios = {
  before_id?: string;
  limit?: number;
  actor_id?: string;
  entity_type?: string;
};

export const servicioRegistroCambios = {
  async list(projectId: string, params: ParametrosRegistroCambios = {}): Promise<PaginaRegistroCambios> {
    const response = await clienteApi.get<PaginaRegistroCambios>(`/projects/${projectId}/change-log`, {
      params,
    });
    return response.data;
  },
};
