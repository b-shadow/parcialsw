import { create } from "zustand";

export type ModoTema = "light" | "dark";

function initialTheme(): ModoTema {
  const stored = window.localStorage.getItem("case_theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
}

function applyTheme(mode: ModoTema) {
  document.documentElement.classList.toggle("dark", mode === "dark");
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem("case_theme", mode);
}

type ThemeState = {
  mode: ModoTema;
  setMode: (mode: ModoTema) => void;
  toggleMode: () => void;
};

export const useAlmacenTema = create<ThemeState>((set, get) => {
  const mode = initialTheme();
  applyTheme(mode);
  return {
    mode,
    setMode: (nextMode) => {
      applyTheme(nextMode);
      set({ mode: nextMode });
    },
    toggleMode: () => {
      const nextMode = get().mode === "dark" ? "light" : "dark";
      applyTheme(nextMode);
      set({ mode: nextMode });
    }
  };
});
