import { apiClient } from "../../../core/api/client";
import type { User } from "../types/user";

export const userService = {
  async list() {
    const response = await apiClient.get<User[]>("/users");
    return response.data;
  }
};
