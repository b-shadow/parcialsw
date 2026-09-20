import { create } from "zustand";

export type ThemeMode = "light" | "dark";

function initialTheme(): ThemeMode {
  const stored = window.localStorage.getItem("case_theme");
  if (stored === "light" || stored === "dark") {
    return stored;
  }
  if (typeof window.matchMedia === "function") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return "light";
}

function applyTheme(mode: ThemeMode) {
  document.documentElement.classList.toggle("dark", mode === "dark");
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem("case_theme", mode);
}

type ThemeState = {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggleMode: () => void;
};

export const useThemeStore = create<ThemeState>((set, get) => {
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
