import { create } from "zustand";

export type UsuarioAutenticado = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  last_access_at: string | null;
  created_at: string;
  role_names: string[];
  status?: string;
};

type AuthState = {
  token: string | null;
  user: UsuarioAutenticado | null;
  establecerToken: (token: string | null) => void;
  establecerUsuario: (user: UsuarioAutenticado | null) => void;
  logout: () => void;
};

export const useAlmacenAutenticacion = create<AuthState>((set) => ({
  token: window.localStorage.getItem("case_access_token"),
  user: null,
  establecerToken: (token) => {
    if (token) {
      window.localStorage.setItem("case_access_token", token);
    } else {
      window.localStorage.removeItem("case_access_token");
    }
    set({ token });
  },
  establecerUsuario: (user) => set({ user }),
  logout: () => {
    window.localStorage.removeItem("case_access_token");
    set({ token: null, user: null });
  }
}));
