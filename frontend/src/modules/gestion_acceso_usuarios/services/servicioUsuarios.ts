import { clienteApi } from "../../../core/api/cliente";
import type { RegistroAuditoria, Rol, Usuario } from "../types/usuario";

export const servicioUsuarios = {
  async list() {
    const response = await clienteApi.get<Usuario[]>("/users");
    return response.data;
  },
  async listRoles() {
    const response = await clienteApi.get<Rol[]>("/users/roles");
    return response.data;
  },
  async updateUser(
    userId: string,
    payload: { full_name?: string; is_active?: boolean; role_name?: Rol["name"] }
  ) {
    const response = await clienteApi.patch<Usuario>(`/users/${userId}`, payload);
    return response.data;
  },
  async listAuditLogs(params?: {
    module?: string;
    action?: string;
    user_id?: string;
    project_id?: string;
    limit?: number;
  }) {
    const response = await clienteApi.get<RegistroAuditoria[]>("/users/audit-logs", { params });
    return response.data;
  },
  async changePassword(payload: { current_password: string; new_password: string }) {
    await clienteApi.patch("/users/me/password", payload);
  }
};
