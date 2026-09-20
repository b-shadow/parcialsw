import { Moon, Sun } from "lucide-react";

import { useThemeStore } from "../../core/theme/themeStore";
import { cn } from "../utils/cn";

type ThemeToggleProps = {
  className?: string;
};

export function ThemeToggle({ className }: ThemeToggleProps) {
  const mode = useThemeStore((state) => state.mode);
  const toggleMode = useThemeStore((state) => state.toggleMode);
  const isDark = mode === "dark";

  return (
    <button
      aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className={cn(
        "inline-flex h-11 items-center gap-2 rounded-full border px-2 shadow-sm transition",
        isDark
          ? "border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
          : "border-teal-500/70 bg-white text-slate-700 hover:bg-teal-50",
        className
      )}
      onClick={toggleMode}
      title={isDark ? "Modo oscuro activo" : "Modo claro activo"}
      type="button"
    >
      <Sun className={cn("h-4 w-4", !isDark ? "text-accent" : "text-slate-400")} aria-hidden="true" />
      <span className={cn("relative h-7 w-14 rounded-full p-1 transition", isDark ? "bg-slate-800" : "bg-teal-50 ring-1 ring-teal-200")}>
        <span
          className={cn(
            "block h-5 w-5 rounded-full bg-teal-300 shadow-sm transition-transform",
            isDark ? "translate-x-7" : "translate-x-0"
          )}
        />
      </span>
      <Moon className={cn("h-4 w-4", isDark ? "text-accent" : "text-slate-400")} aria-hidden="true" />
    </button>
  );
}
