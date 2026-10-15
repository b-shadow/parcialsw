import { useEffect, useState } from "react";
import { Bell, BellOff, LoaderCircle } from "lucide-react";

import {
  pushNotificationService,
  type PushNotificationState
} from "../../core/notifications/pushNotificationService";
import { cn } from "../utils/cn";

export function PushNotificationButton() {
  const [state, setState] = useState<PushNotificationState>("disabled");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("Consultando notificaciones...");

  useEffect(() => {
    pushNotificationService.state()
      .then((nextState) => {
        setState(nextState);
        setMessage(
          nextState === "subscribed"
            ? "Desactivar notificaciones"
            : nextState === "available"
              ? "Activar notificaciones"
              : nextState === "unsupported"
                ? "El navegador no admite notificaciones"
                : "Notificaciones no configuradas en el servidor"
        );
      })
      .catch(() => setMessage("No se pudo consultar el estado de notificaciones"))
      .finally(() => setLoading(false));
  }, []);

  async function toggleNotifications() {
    if (loading || state === "unsupported" || state === "disabled") {
      return;
    }
    setLoading(true);
    try {
      if (state === "subscribed") {
        await pushNotificationService.unsubscribe();
        setState("available");
        setMessage("Activar notificaciones");
      } else {
        await pushNotificationService.subscribe();
        setState("subscribed");
        setMessage("Desactivar notificaciones");
        await pushNotificationService.sendTest();
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo cambiar la suscripcion");
    } finally {
      setLoading(false);
    }
  }

  const Icon = loading ? LoaderCircle : state === "subscribed" ? Bell : BellOff;
  return (
    <button
      aria-label={message}
      className={cn(
        "flex h-10 w-10 items-center justify-center rounded-full border transition",
        state === "subscribed"
          ? "border-teal-500 bg-teal-50 text-teal-700 dark:bg-teal-400/10 dark:text-teal-300"
          : "border-slate-300 text-slate-500 dark:border-slate-700 dark:text-slate-400",
        (state === "disabled" || state === "unsupported") && "cursor-not-allowed opacity-60"
      )}
      disabled={loading || state === "disabled" || state === "unsupported"}
      onClick={toggleNotifications}
      title={message}
      type="button"
    >
      <Icon className={loading ? "animate-spin" : ""} size={18} aria-hidden="true" />
    </button>
  );
}
