import { create } from "zustand";

export type ModoTema = "light" | "dark";

function temaInicial(): ModoTema {
  const stored = window.localStorage.getItem("case_theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
}

function aplicarTema(mode: ModoTema) {
  document.documentElement.classList.toggle("dark", mode === "dark");
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem("case_theme", mode);
}

type ThemeState = {
  mode: ModoTema;
  establecerModo: (mode: ModoTema) => void;
  alternarModo: () => void;
};

export const useAlmacenTema = create<ThemeState>((set, get) => {
  const mode = temaInicial();
  aplicarTema(mode);
  return {
    mode,
    establecerModo: (nextMode) => {
      aplicarTema(nextMode);
      set({ mode: nextMode });
    },
    alternarModo: () => {
      const nextMode = get().mode === "dark" ? "light" : "dark";
      aplicarTema(nextMode);
      set({ mode: nextMode });
    }
  };
});
