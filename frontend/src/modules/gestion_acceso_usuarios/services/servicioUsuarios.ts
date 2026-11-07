import { clienteApi } from "../../../core/api/cliente";
import type { RegistroAuditoria, Rol, Usuario } from "../types/usuario";

export const servicioUsuarios = {
  async listar() {
    const response = await clienteApi.get<Usuario[]>("/users");
    return response.data;
  },
  async listarRoles() {
    const response = await clienteApi.get<Rol[]>("/users/roles");
    return response.data;
  },
  async actualizarUsuario(
    userId: string,
    payload: { full_name?: string; is_active?: boolean; role_name?: Rol["name"] }
  ) {
    const response = await clienteApi.patch<Usuario>(`/users/${userId}`, payload);
    return response.data;
  },
  async listarBitacora(params?: {
    module?: string;
    action?: string;
    user_id?: string;
    project_id?: string;
    limit?: number;
  }) {
    const response = await clienteApi.get<RegistroAuditoria[]>("/users/audit-logs", { params });
    return response.data;
  },
  async cambiarContrasena(payload: { current_password: string; new_password: string }) {
    await clienteApi.patch("/users/me/password", payload);
  }
};
