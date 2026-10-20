import { apiClient } from "../../../core/api/client";
import type { ChangeLogPage } from "../../../core/contracts/mejoras2p";

export type ListChangeLogParams = {
  before_id?: string;
  limit?: number;
  actor_id?: string;
  entity_type?: string;
};

export const changeLogService = {
  async list(projectId: string, params: ListChangeLogParams = {}): Promise<ChangeLogPage> {
    const response = await apiClient.get<ChangeLogPage>(`/projects/${projectId}/change-log`, {
      params,
    });
    return response.data;
  },
};
