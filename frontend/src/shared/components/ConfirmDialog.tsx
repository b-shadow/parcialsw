import { useEffect, useRef } from "react";
import { create } from "zustand";
import { AlertCircle } from "lucide-react";
import { cn } from "../utils/cn";

export type ConfirmOptions = {
  title: string;
  description: string;
  confirmLabel: string;
  tone?: "danger" | "primary";
};

type ConfirmStore = {
  options: ConfirmOptions | null;
  resolve: ((value: boolean) => void) | null;
  open: (opts: ConfirmOptions) => Promise<boolean>;
  close: (result: boolean) => void;
};

export const useConfirmStore = create<ConfirmStore>((set, get) => ({
  options: null,
  resolve: null,
  open: (opts) => {
    return new Promise<boolean>((resolve) => {
      set({ options: opts, resolve });
    });
  },
  close: (result) => {
    const { resolve } = get();
    if (resolve) resolve(result);
    set({ options: null, resolve: null });
  },
}));

export function useConfirm(): (opts: ConfirmOptions) => Promise<boolean> {
  return useConfirmStore.getState().open;
}

export function ConfirmDialogHost() {
  const options = useConfirmStore((state) => state.options);
  const close = useConfirmStore((state) => state.close);
  const cancelBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!options) return;
    cancelBtnRef.current?.focus();

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        close(false);
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [options, close]);

  if (!options) return null;

  const isDanger = options.tone === "danger";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm"
      onClick={() => close(false)}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-description"
        className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-4">
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
              isDanger
                ? "bg-rose-100 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400"
                : "bg-teal-100 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400"
            )}
          >
            <AlertCircle size={22} />
          </div>
          <div className="min-w-0 flex-1">
            <h3
              id="confirm-dialog-title"
              className="text-base font-bold text-slate-900 dark:text-white"
            >
              {options.title}
            </h3>
            <p
              id="confirm-dialog-description"
              className="mt-2 text-sm text-slate-600 dark:text-slate-400"
            >
              {options.description}
            </p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            ref={cancelBtnRef}
            type="button"
            onClick={() => close(false)}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => close(true)}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors",
              isDanger
                ? "bg-rose-600 hover:bg-rose-700 dark:bg-rose-600 dark:hover:bg-rose-500"
                : "bg-teal-600 hover:bg-teal-700 dark:bg-teal-600 dark:hover:bg-teal-500"
            )}
          >
            {options.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
