import { apiClient } from "../../../core/api/client";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/user";

export const authService = {
  async login(payload: LoginPayload) {
    const response = await apiClient.post<TokenResponse>("/auth/login", payload);
    return response.data;
  },
  async register(payload: RegisterPayload) {
    const response = await apiClient.post<User>("/auth/register", payload);
    return response.data;
  },
  async me() {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },
  async listUsers() {
    const response = await apiClient.get<User[]>("/users");
    return response.data;
  }
};
