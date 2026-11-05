import { clienteApi } from "../../../core/api/cliente";
import type { CargaIngreso, CargaRegistro, RespuestaToken, Usuario } from "../types/usuario";

export const servicioAutenticacion = {
  async login(payload: CargaIngreso) {
    const response = await clienteApi.post<RespuestaToken>("/auth/login", payload);
    return response.data;
  },
  async register(payload: CargaRegistro) {
    const response = await clienteApi.post<Usuario>("/auth/register", payload);
    return response.data;
  },
  async me() {
    const response = await clienteApi.get<Usuario>("/auth/me");
    return response.data;
  },
  async listUsers() {
    const response = await clienteApi.get<Usuario[]>("/users");
    return response.data;
  }
};
