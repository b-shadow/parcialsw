import { apiClient } from "../../../core/api/client";
import type { AuditLog, Role, User } from "../types/user";

export const userService = {
  async list() {
    const response = await apiClient.get<User[]>("/users");
    return response.data;
  },
  async listRoles() {
    const response = await apiClient.get<Role[]>("/users/roles");
    return response.data;
  },
  async updateUser(
    userId: string,
    payload: { full_name?: string; is_active?: boolean; role_name?: Role["name"] }
  ) {
    const response = await apiClient.patch<User>(`/users/${userId}`, payload);
    return response.data;
  },
  async listAuditLogs(params?: {
    module?: string;
    action?: string;
    user_id?: string;
    project_id?: string;
    limit?: number;
  }) {
    const response = await apiClient.get<AuditLog[]>("/users/audit-logs", { params });
    return response.data;
  },
  async changePassword(payload: { current_password: string; new_password: string }) {
    await apiClient.patch("/users/me/password", payload);
  }
};
