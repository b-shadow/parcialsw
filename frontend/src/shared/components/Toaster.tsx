import { create } from "zustand";
import { AlertCircle, AlertTriangle, CheckCircle2, X } from "lucide-react";
import { cn } from "../utils/cn";

export type Toast = {
  id: string;
  title: string;
  text?: string;
  tone: "accent" | "amber" | "rose";
};

type ToastState = {
  items: Toast[];
  push: (t: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
};

export const useToast = create<ToastState>((set) => ({
  items: [],
  push: (t) => {
    const id = Math.random().toString(36).slice(2, 9);
    set((state) => ({ items: [...state.items, { ...t, id }] }));
    setTimeout(() => {
      set((state) => ({ items: state.items.filter((item) => item.id !== id) }));
    }, 4000);
  },
  dismiss: (id) =>
    set((state) => ({ items: state.items.filter((item) => item.id !== id) })),
}));

export const toast = {
  success: (title: string, text?: string) =>
    useToast.getState().push({ title, text, tone: "accent" }),
  warning: (title: string, text?: string) =>
    useToast.getState().push({ title, text, tone: "amber" }),
  error: (title: string, text?: string) =>
    useToast.getState().push({ title, text, tone: "rose" }),
};

export function Toaster() {
  const items = useToast((state) => state.items);
  const dismiss = useToast((state) => state.dismiss);

  const visible = items.slice(-4);

  return (
    <aside
      aria-live="polite"
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex max-w-sm flex-col gap-2"
    >
      {visible.map((item) => {
        const toneBorder =
          item.tone === "accent"
            ? "border-l-4 border-l-teal-600 dark:border-l-teal-400"
            : item.tone === "amber"
            ? "border-l-4 border-l-amber-500 dark:border-l-amber-400"
            : "border-l-4 border-l-rose-600 dark:border-l-rose-400";

        const Icon =
          item.tone === "accent"
            ? CheckCircle2
            : item.tone === "amber"
            ? AlertTriangle
            : AlertCircle;

        const iconColor =
          item.tone === "accent"
            ? "text-teal-600 dark:text-teal-400"
            : item.tone === "amber"
            ? "text-amber-500 dark:text-amber-400"
            : "text-rose-600 dark:text-rose-400";

        return (
          <div
            key={item.id}
            role="status"
            className={cn(
              "pointer-events-auto flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-lg transition-all dark:border-slate-800 dark:bg-slate-900",
              toneBorder
            )}
          >
            <Icon size={20} className={cn("mt-0.5 shrink-0", iconColor)} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {item.title}
              </p>
              {item.text && (
                <p className="mt-0.5 text-xs text-slate-600 dark:text-slate-400">
                  {item.text}
                </p>
              )}
            </div>
            <button
              onClick={() => dismiss(item.id)}
              className="shrink-0 rounded p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
              title="Cerrar aviso"
              aria-label="Cerrar aviso"
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </aside>
  );
}
