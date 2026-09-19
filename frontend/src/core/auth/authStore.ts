import { create } from "zustand";

export type AuthUser = {
  id: string;
  email: string;
  full_name: string;
  status: string;
};

type AuthState = {
  token: string | null;
  user: AuthUser | null;
  setToken: (token: string | null) => void;
  setUser: (user: AuthUser | null) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: window.localStorage.getItem("case_access_token"),
  user: null,
  setToken: (token) => {
    if (token) {
      window.localStorage.setItem("case_access_token", token);
    } else {
      window.localStorage.removeItem("case_access_token");
    }
    set({ token });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    window.localStorage.removeItem("case_access_token");
    set({ token: null, user: null });
  }
}));
