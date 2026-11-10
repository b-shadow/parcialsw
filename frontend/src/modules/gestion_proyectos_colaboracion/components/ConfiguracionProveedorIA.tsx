import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Settings, X } from "lucide-react";
import { servicioFase1 } from "../../../core/api/servicioFase1";
import type { ProveedorIA } from "../../../core/contracts/mejoras2p";
import type { EstadoProveedorIA } from "../../../core/contracts/phase1";
import { toast } from "../../../shared/components/Notificador";
import { cn } from "../../../shared/utils/cn";

export interface PropiedadesConfiguracionProveedorIA {
  projectId: string;
  current: ProveedorIA;
  currentSource: "local" | "aws";
  onChange(p: ProveedorIA): void;
  onSourceChange(source: "local" | "aws"): void;
  isOpen?: boolean;
  onClose?: () => void;
}

interface ProviderOption {
  id: ProveedorIA;
  title: string;
  subtitle: string;
  badge: string;
  badgeColor: string;
  dataProv: string;
}

const PROVIDERS: ProviderOption[] = [
  {
    id: "ollama",
    title: "Ollama del proyecto",
    subtitle: "Motor configurado para el proyecto",
    badge: "Proyecto",
    badgeColor: "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300",
    dataProv: "Ollama · modelo del proyecto",
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

export function ConfiguracionProveedorIA({
  projectId,
  current,
  currentSource,
  onChange,
  onSourceChange,
  isOpen: controlledIsOpen,
  onClose: controlledOnClose,
}: PropiedadesConfiguracionProveedorIA) {
  const [internalOpen, setInternalOpen] = useState(false);
  const [health, setHealth] = useState<EstadoProveedorIA | null>(null);
  const [loading, setLoading] = useState(false);

  const isControlled = controlledIsOpen !== undefined;
  const open = isControlled ? controlledIsOpen : internalOpen;

  const manejarCierre = () => {
    if (isControlled) {
      controlledOnClose?.();
    } else {
      setInternalOpen(false);
    }
  };

  const manejarAlternancia = () => {
    if (isControlled) {
      if (open) controlledOnClose?.();
    } else {
      setInternalOpen((v) => !v);
    }
  };

  useEffect(() => {
    if (open) {
      setLoading(true);
      Promise.all([servicioFase1.configuracionIA(projectId), servicioFase1.estadoProveedorIA(projectId)])
        .then(([settings, data]) => {
          onChange(settings.preferred_provider);
          onSourceChange(settings.settings_json.origen_ollama === "aws" ? "aws" : "local");
          setHealth(data);
        })
        .catch(() => setHealth(null))
        .finally(() => setLoading(false));
    }
  }, [open, projectId]);

  useEffect(() => {
    function alPulsarTecla(e: KeyboardEvent) {
      if (e.key === "Escape" && open) {
        manejarCierre();
      }
    }
    if (open) {
      window.addEventListener("keydown", alPulsarTecla);
    }
    return () => {
      window.removeEventListener("keydown", alPulsarTecla);
    };
  }, [open]);

  const guardarSeleccion = async (providerId: ProveedorIA, source: "local" | "aws") => {
    if (loading || !health || (providerId === "gemini" && !health.gemini_configured) ||
        (providerId === "ollama" && !health.configured_sources?.includes(source))) return;
    setLoading(true);
    try {
      const settings = await servicioFase1.configuracionIA(projectId);
      await servicioFase1.actualizarConfiguracionIA(projectId, {
        enabled: settings.enabled,
        preferred_provider: providerId,
        fallback_enabled: settings.fallback_enabled,
        require_confirmation: settings.require_confirmation,
        model_name: providerId === settings.preferred_provider
          ? settings.model_name
          : providerId === "gemini" ? "gemini-2.5-flash" : providerId === "rule_engine" ? "deterministic-v2" : "qwen2.5-coder:1.5b",
        max_context_messages: settings.max_context_messages,
        summary_trigger_messages: settings.summary_trigger_messages,
        settings_json: { ...settings.settings_json, origen_ollama: source },
      });
      toast.success("IA del proyecto actualizada", providerId === "ollama" ? `Ollama ${source === "aws" ? "en AWS" : "local"}` : providerId);
      onChange(providerId);
      onSourceChange(source);
      manejarCierre();
    } catch {
      toast.error("Error al actualizar proveedor", "No se pudieron guardar los ajustes de la IA");
    } finally {
      setLoading(false);
    }
  };

  const seleccionarProveedor = (providerId: ProveedorIA) => guardarSeleccion(providerId, currentSource);

  return (
    <div className="relative inline-block">
      {!isControlled && (
        <button
          type="button"
          onClick={manejarAlternancia}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-slate-300 bg-white text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
          aria-label="Ajustes de la IA"
          aria-expanded={open}
          title="Ajustes de la IA"
        >
          <Settings size={16} />
        </button>
      )}

      {open && createPortal(
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/55 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) manejarCierre(); }}>
        <div role="dialog" aria-modal="true" aria-label="Proveedor de la IA del proyecto" className="w-full max-w-sm max-h-[min(90vh,680px)] overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 text-slate-900 shadow-2xl dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100">
          <div className="mb-2 flex items-center justify-between border-b border-slate-100 pb-2 dark:border-slate-800">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Proveedor de la IA del proyecto
            </h4>
            <button
              type="button"
              onClick={manejarCierre}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              aria-label="Cerrar ajustes"
            >
              <X size={14} />
            </button>
          </div>

          <div role="radiogroup" aria-label="Proveedor de IA" className="space-y-1.5">
            {PROVIDERS.map((prov) => {
              const isSelected = current === prov.id;
              const disabled = loading || !health ||
                (prov.id === "gemini" && !health.gemini_configured) ||
                (prov.id === "ollama" && !health.configured_sources?.length);
              let statusText = prov.subtitle;

              if (prov.id === "gemini" && health && !health.gemini_configured) statusText = "No configurado en el servidor";
              if (prov.id === "ollama" && health && !health.configured_sources?.length) statusText = "No hay un origen Ollama configurado";

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
                  tabIndex={disabled ? -1 : 0}
                  aria-checked={isSelected}
                  aria-disabled={disabled}
                  data-prov={prov.dataProv}
                  onClick={() => { if (!disabled) void seleccionarProveedor(prov.id); }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      if (!disabled) void seleccionarProveedor(prov.id);
                    }
                  }}
                  className={cn(
                    "flex cursor-pointer items-start justify-between gap-3 rounded-lg border p-2.5 text-left transition disabled:opacity-50",
                    disabled && "cursor-not-allowed opacity-50",
                    isSelected
                      ? "border-teal-500 bg-teal-50/50 dark:border-teal-600 dark:bg-teal-950/20"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600 dark:hover:bg-slate-800"
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

          {current === "ollama" && (
            <div className="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
              <p className="mb-2 text-xs font-semibold text-slate-700 dark:text-slate-200">Origen compartido del proyecto</p>
              <div className="grid grid-cols-2 gap-2">
                {(["local", "aws"] as const).map((source) => (
                  <button
                    key={source}
                    type="button"
                    aria-pressed={currentSource === source}
                    disabled={loading || !health?.configured_sources?.includes(source)}
                    onClick={() => void guardarSeleccion("ollama", source)}
                    className={cn(
                      "rounded-md border px-2 py-1.5 text-xs disabled:cursor-not-allowed disabled:opacity-50",
                      currentSource === source ? "border-teal-500 bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200" : "border-slate-300 bg-white text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                    )}
                  >
                    {source === "local" ? "Local" : "AWS"}
                  </button>
                ))}
              </div>
            </div>
          )}

        </div>
        </div>, document.body
      )}
    </div>
  );
}
