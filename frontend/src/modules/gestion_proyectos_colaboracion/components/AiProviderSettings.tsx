import { useEffect, useRef, useState } from "react";
import { Settings, X } from "lucide-react";
import { phase1Service } from "../../../core/api/phase1Service";
import type { AiProvider } from "../../../core/contracts/mejoras2p";
import type { AiProviderHealth } from "../../../core/contracts/phase1";
import { toast } from "../../../shared/components/Toaster";
import { cn } from "../../../shared/utils/cn";

export interface AiProviderSettingsProps {
  projectId: string;
  current: AiProvider;
  onChange(p: AiProvider): void;
  isOpen?: boolean;
  onClose?: () => void;
}

interface ProviderOption {
  id: AiProvider;
  title: string;
  subtitle: string;
  badge: string;
  badgeColor: string;
  dataProv: string;
}

const PROVIDERS: ProviderOption[] = [
  {
    id: "ollama",
    title: "Ollama local",
    subtitle: "Sin internet · modelos locales (Qwen)",
    badge: "Local",
    badgeColor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    dataProv: "Ollama · qwen2.5-coder:1.5b",
  },
  {
    id: "gemini",
    title: "Gemini (AI Studio)",
    subtitle: "Requiere GEMINI_API_KEY en el servidor",
    badge: "Nube",
    badgeColor: "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300",
    dataProv: "Gemini · AI Studio",
  },
  {
    id: "rule_engine",
    title: "Motor de reglas",
    subtitle: "Respaldo sin modelo · siempre disponible",
    badge: "Respaldo",
    badgeColor: "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300",
    dataProv: "Motor de reglas",
  },
];

export function AiProviderSettings({
  projectId,
  current,
  onChange,
  isOpen: controlledIsOpen,
  onClose: controlledOnClose,
}: AiProviderSettingsProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [health, setHealth] = useState<AiProviderHealth | null>(null);
  const [loading, setLoading] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  const isControlled = controlledIsOpen !== undefined;
  const open = isControlled ? controlledIsOpen : internalOpen;

  const handleClose = () => {
    if (isControlled) {
      controlledOnClose?.();
    } else {
      setInternalOpen(false);
    }
  };

  const handleToggle = () => {
    if (isControlled) {
      if (open) controlledOnClose?.();
    } else {
      setInternalOpen((v) => !v);
    }
  };

  useEffect(() => {
    if (open) {
      setLoading(true);
      phase1Service
        .aiProviderHealth(projectId)
        .then((data) => setHealth(data))
        .catch(() => setHealth(null))
        .finally(() => setLoading(false));
    }
  }, [open, projectId]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape" && open) {
        handleClose();
      }
    }
    function onClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        handleClose();
      }
    }
    if (open) {
      window.addEventListener("keydown", onKeyDown);
      window.addEventListener("mousedown", onClickOutside);
    }
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("mousedown", onClickOutside);
    };
  }, [open]);

  const selectProvider = async (providerId: AiProvider) => {
    try {
      await phase1Service.updateAiSettings(projectId, {
        enabled: true,
        preferred_provider: providerId,
        fallback_enabled: true,
        require_confirmation: true,
        model_name: providerId === "gemini" ? "gemini-2.5-flash" : "qwen2.5-coder:7b",
        max_context_messages: 40,
        summary_trigger_messages: 30,
        settings_json: {},
      });
      toast.success("Proveedor actualizado", `El proyecto ahora usa ${providerId}`);
      onChange(providerId);
      handleClose();
    } catch {
      toast.error("Error al actualizar proveedor", "No se pudieron guardar los ajustes de la IA");
    }
  };

  return (
    <div className="relative inline-block" ref={popoverRef}>
      {!isControlled && (
        <button
          type="button"
          onClick={handleToggle}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          aria-label="Ajustes de la IA"
          aria-expanded={open}
          title="Ajustes de la IA"
        >
          <Settings size={16} />
        </button>
      )}

      {open && (
        <div
          role="radiogroup"
          aria-label="Proveedor de IA"
          className="absolute right-0 top-full z-50 mt-2 w-80 rounded-xl border border-slate-200 bg-white p-3 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
        >
          <div className="mb-2 flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Proveedor de la IA del proyecto
            </h4>
            <button
              type="button"
              onClick={handleClose}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              aria-label="Cerrar ajustes"
            >
              <X size={14} />
            </button>
          </div>

          <div className="space-y-1.5">
            {PROVIDERS.map((prov) => {
              const isSelected = current === prov.id;
              let statusText = prov.subtitle;

              if (health && health.provider === prov.id) {
                if (health.available) {
                  statusText = `Disponible · ${health.latency_ms ?? 0} ms`;
                } else {
                  statusText = health.error_message || "No disponible";
                }
              }

              return (
                <div
                  key={prov.id}
                  role="radio"
                  tabIndex={0}
                  aria-checked={isSelected}
                  data-prov={prov.dataProv}
                  onClick={() => void selectProvider(prov.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      void selectProvider(prov.id);
                    }
                  }}
                  className={cn(
                    "flex cursor-pointer items-start justify-between gap-3 rounded-lg border p-2.5 transition text-left",
                    isSelected
                      ? "border-teal-500 bg-teal-50/50 dark:border-teal-600 dark:bg-teal-950/20"
                      : "border-slate-100 hover:border-slate-200 hover:bg-slate-50 dark:border-slate-800/60 dark:hover:border-slate-700 dark:hover:bg-slate-800/40"
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    <span
                      className={cn(
                        "mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition",
                        isSelected
                          ? "border-teal-600 bg-teal-600 text-white"
                          : "border-slate-400 bg-white dark:border-slate-600 dark:bg-slate-800"
                      )}
                    >
                      {isSelected && <span className="h-1.5 w-1.5 rounded-full bg-white" />}
                    </span>
                    <div>
                      <b className="block text-xs font-semibold text-slate-800 dark:text-slate-100">
                        {prov.title}
                      </b>
                      <small className="block text-[11px] text-slate-500 dark:text-slate-400">
                        {loading && prov.id === current ? "Comprobando salud..." : statusText}
                      </small>
                    </div>
                  </div>
                  <span className={cn("shrink-0 rounded px-1.5 py-0.5 text-[10px] font-bold", prov.badgeColor)}>
                    {prov.badge}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-2.5 pt-2 border-t border-slate-100 text-right dark:border-slate-800">
            <span className="text-[10px] text-slate-400">AiProviderSettings · V1.8</span>
          </div>
        </div>
      )}
    </div>
  );
}
